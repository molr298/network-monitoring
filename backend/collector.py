"""Background thread that periodically pulls metrics from Zabbix and stores
   them in TimescaleDB / PostgreSQL.

   NOTE: This is a minimal first-cut implementation aimed at providing a working
   data-collection pipeline for the MVP. The logic can be optimized and
   hardened later (pagination, error back-off, async HTTP, etc.).
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import List

import requests
from sqlalchemy import insert

from database import engine, init_db, metrics_table

ZABBIX_API_URL = os.getenv("ZABBIX_API_URL", "http://zabbix-server/api_jsonrpc.php")
ZABBIX_USER = os.getenv("ZABBIX_USER", "Admin")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "zabbix")

# Comma-separated list of item keys to collect. Extend as needed.
DEFAULT_KEYS = (
    "system.cpu.util,vm.memory.size[available],vm.memory.size[total],net.if.in[eth0],net.if.out[eth0]"
)
METRIC_KEYS: List[str] = [k.strip() for k in os.getenv("METRIC_KEYS", DEFAULT_KEYS).split(",") if k.strip()]

COLLECT_INTERVAL = int(os.getenv("COLLECT_INTERVAL", "60"))  # seconds


class ZabbixAPI:
    """Minimal Zabbix API wrapper (JSON-RPC 2.0)."""

    def __init__(self):
        self.auth_token: str | None = None

    def _request(self, method: str, params: dict, auth: bool = True):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
        if auth and self.auth_token:
            payload["auth"] = self.auth_token
        headers = {"Content-Type": "application/json"}
        resp = requests.post(ZABBIX_API_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        res = resp.json()
        if "error" in res:
            raise RuntimeError(res["error"])
        return res["result"]

    def login(self):
        self.auth_token = self._request(
            "user.login", {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD}, auth=False
        )

    def host_get(self):
        # Request both technical host ("host") and visible name ("name")
        return self._request("host.get", {"output": ["hostid", "host", "name"]}, auth=True)

    def item_get(self, host_id, keys):
        return self._request(
            "item.get",
            {
                "output": ["key_", "lastvalue"],
                "hostids": [host_id],
                "filter": {"key_": keys},
                "sortfield": "name",
            },
            auth=True,
        )

    def problem_get(self):
        return self._request(
            "trigger.get",
            {
                "output": ["triggerid", "description", "priority"],
                "filter": {"value": 1},  # 1 = Problem state
                "selectHosts": ["host"],
                "expandDescription": 1,
                "sortfield": "lastchange",
                "sortorder": "DESC",
            },
            auth=True,
        )

    def get_problem_by_id(self, trigger_id: str):
        return self._request(
            "trigger.get",
            {
                "output": ["triggerid", "description", "priority"],
                "triggerids": [trigger_id],
                "selectHosts": ["host"],
                "expandDescription": 1,
            },
            auth=True,
        )

    def execute_script(self, script_id: str, host_id: str):
        """Executes a script on a given host."""
        return self._request(
            "script.execute",
            {
                "scriptid": script_id,
                "hostid": host_id,
            },
            auth=True,
        )


class ZabbixCollector(threading.Thread):
    """Collect metrics from Zabbix periodically."""

    def __init__(self):
        super().__init__(daemon=True)
        init_db()
        self.api = ZabbixAPI()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            try:
                if not self.api.auth_token:
                    self.api.login()
                self.collect_once()
            except Exception as exc:  # noqa: BLE001
                print(f"[Collector] error: {exc}")
                # Force re-login next loop
                self.api.auth_token = None
            finally:
                self._stop_event.wait(COLLECT_INTERVAL)

    def collect_once(self):
        hosts = self.api.host_get()
        now = datetime.now(timezone.utc)
        rows = []
        print(f"[Collector] found {len(hosts)} host(s) to collect data from")
        for host in hosts:
            host_id = host["hostid"]
            items = self.api.item_get(host_id, METRIC_KEYS)
            print(f"[Collector] host {host_id} has {len(items)} matching item(s)")
            for item in items:
                raw_val = str(item.get("lastvalue", "")).strip()
                # extract leading numeric part, allow decimals
                import re
                m = re.match(r"[-+]?[0-9]*\.?[0-9]+", raw_val)
                if not m:
                    continue  # skip non-numeric
                value = float(m.group(0))
                rows.append(
                    {
                        "host_id": host_id,
                        "item_key": item["key_"],
                        "value": value,
                        "timestamp": now,
                    }
                )
        if rows:
            with engine.begin() as conn:
                conn.execute(insert(metrics_table), rows)
            print(f"[Collector] inserted {len(rows)} rows @ {now.isoformat()}")
