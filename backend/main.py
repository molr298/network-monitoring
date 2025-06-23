from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
import os
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Network Monitoring API",
             description="API for AI-powered network monitoring with Zabbix",
             version="0.1.0")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
ZABBIX_API_URL = os.getenv("ZABBIX_API_URL", "http://zabbix-server/api_jsonrpc.php")
ZABBIX_USER = os.getenv("ZABBIX_USER", "Admin")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "zabbix")

# Authentication token cache
zabbix_auth_token = None

class ZabbixAuth:
    @staticmethod
    def get_auth_token():
        global zabbix_auth_token
        
        if zabbix_auth_token:
            return zabbix_auth_token
            
        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": ZABBIX_USER,
                "password": ZABBIX_PASSWORD
            },
            "id": 1
        }
        
        try:
            response = requests.post(ZABBIX_API_URL, json=data, headers=headers)
            response.raise_for_status()
            zabbix_auth_token = response.json().get("result")
            return zabbix_auth_token
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to authenticate with Zabbix: {str(e)}")

# API Models
class HostStatus(BaseModel):
    host_id: str
    name: str
    status: str
    last_check: datetime
    issues: List[str] = []

class NetworkMetrics(BaseModel):
    timestamp: datetime
    host_id: str
    cpu_usage: float
    memory_usage: float  # available bytes
    memory_total: float | None = None  # total bytes, may be None if not collected
    network_in: float
    network_out: float


class HostKeys(BaseModel):
    host_id: str
    keys: List[str]

class Alert(BaseModel):
    id: str
    host: str
    hostid: str
    name: str
    severity: int

class Anomaly(BaseModel):
    id: int
    host_id: str
    item_key: str
    value: float
    timestamp: datetime
    reason: Optional[str] = None

class RemediationRequest(BaseModel):
    script_id: str
    host_id: str


class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    recipients: str  # Comma-separated

# Start background collector
from collector import ZabbixCollector, ZabbixAPI
from email_notifier import EmailNotifier
from config import get_email_config as load_email_config_from_file, save_email_config as save_email_config_to_file
from ai_analyzer import AIAnalyzer
from anomaly_detector import AnomalyDetector

collector_thread: ZabbixCollector | None = None
email_notifier_thread: EmailNotifier | None = None
ai_analyzer_thread: AIAnalyzer | None = None
anomaly_detector_thread: AnomalyDetector | None = None

@app.on_event("startup")
async def _startup():
    """Initializes and starts background threads for data collection and notifications."""
    global collector_thread, email_notifier_thread, ai_analyzer_thread, anomaly_detector_thread
    
    # Start Zabbix Collector
    try:
        if collector_thread is None:
            collector_thread = ZabbixCollector()
            collector_thread.start()
            logger.info("Zabbix collector thread started.")
    except Exception as e:
        logger.error(f"Failed to start Zabbix collector: {e}", exc_info=True)

    # Initialize AI Analyzer
    try:
        google_api_key = os.getenv("GOOGLE_AI_API_KEY")
        ai_analyzer_thread = AIAnalyzer(api_key=google_api_key)
        logger.info("AI Analyzer initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize AI Analyzer: {e}", exc_info=True)
        ai_analyzer_thread = None  # Ensure it's None if failed

    # Start Email Notifier
    try:
        if email_notifier_thread is None:
            email_config = load_email_config_from_file()
            email_notifier_thread = EmailNotifier(
                smtp_host=email_config.get("smtp_host"),
                smtp_port=int(email_config.get("smtp_port", 587)),
                smtp_user=email_config.get("smtp_user"),
                smtp_password=email_config.get("smtp_password"),
                recipients=[
                    e.strip() for e in email_config.get("recipients", "").split(",") if e.strip()
                ],
            )
            email_notifier_thread.start()
            logger.info("Email notifier thread started.")
    except Exception as e:
        logger.error(f"Failed to start email notifier: {e}", exc_info=True)

    # Start Anomaly Detector
    try:
        if anomaly_detector_thread is None:
            anomaly_detector_thread = AnomalyDetector()
            anomaly_detector_thread.start()
            logger.info("Anomaly detector thread started.")
    except Exception as e:
        logger.error(f"Failed to start anomaly detector: {e}", exc_info=True)

# API Endpoints

@app.get("/api/config/email", response_model=EmailConfig)
def get_email_config_api():
    """
    Returns the current email configuration.
    """
    return load_email_config_from_file()


@app.post("/api/config/email")
def save_email_config_api(email_config: EmailConfig):
    """
    Saves the email configuration.
    A restart is required for changes to take effect.
    """
    save_email_config_to_file(email_config.dict())
    return {
        "message": "Email configuration saved. Please restart the backend to apply changes."
    }


@app.post("/api/config/email/test")
def test_email_config():
    """
    Sends a test email using the saved configuration.
    """
    config = load_email_config_from_file()
    recipients_str = config.get("recipients", "")
    recipients = [e.strip() for e in recipients_str.split(",") if e.strip()]

    # A sender email is required, but we can create a default if not provided
    smtp_user = config.get("smtp_user") or f"noreply@{config.get('smtp_host', 'local.host')}"

    if not all([config.get("smtp_host"), config.get("smtp_port"), recipients]):
        raise HTTPException(
            status_code=400, detail="SMTP Host, Port, and Recipients are required."
        )

    subject = "[Monitoring] Test Email"
    body = "This is a test email from your network monitoring system. If you received this, your email settings are correct."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)

    try:
        with smtplib.SMTP(config["smtp_host"], int(config["smtp_port"])) as server:
            # Only attempt to log in if a password is provided
            if config.get("smtp_password"):
                server.starttls()
                server.login(config["smtp_user"], config["smtp_password"])
            server.sendmail(smtp_user, recipients, msg.as_string())
        return {"message": f"Test email sent successfully to {recipients_str}!"}
    except Exception as e:
        logger.error("Failed to send test email", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/api/alerts/{alert_id}/analyze")
def analyze_alert_api(alert_id: str, auth: str = Depends(ZabbixAuth.get_auth_token)):
    """
    Provides AI-powered analysis for a specific alert.
    """
    api = ZabbixAPI()
    api.auth_token = auth
    alerts = api.get_problem_by_id(alert_id)
    if not alerts:
        raise HTTPException(status_code=404, detail="Alert not found.")
    target_alert = alerts[0]

    if not target_alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    # Extract relevant data for the AI
    analysis_data = {
        "host": target_alert.get("hosts")[0].get("host") if target_alert.get("hosts") else "Unknown",
        "description": target_alert.get("description"),
        "severity": target_alert.get("priority")
    }

    result = ai_analyzer_thread.analyze_alert(analysis_data)
    return result


@app.get("/api/anomalies", response_model=List[Anomaly])
def get_anomalies():
    """Returns a list of detected anomalies."""
    from database import anomalies_table, engine
    from sqlalchemy import select

    stmt = select(anomalies_table).order_by(anomalies_table.c.timestamp.desc()).limit(100)
    with engine.begin() as conn:
        result = conn.execute(stmt).fetchall()
    return result


def get_zabbix_api():
    api = ZabbixAPI()
    api.login()
    return api

@app.post("/api/alerts/{alert_id}/email")
def send_alert_email(alert_id: str):
    """Send an immediate email notification for a specific alert.

    Works even if the background EmailNotifier thread is not running by
    loading the saved email configuration and sending directly.
    """
    api = ZabbixAPI()
    api.login()
    alert_data = api.get_problem_by_id(trigger_id=alert_id)
    if not alert_data:
        raise HTTPException(status_code=404, detail="Alert not found")
    trigger = alert_data[0]

    # Prefer using the running notifier thread if available
    global email_notifier_thread
    try:
        if email_notifier_thread is not None:
            email_notifier_thread.send_notification(trigger, "PROBLEM")
            return {"status": "email_sent_via_thread"}
    except Exception as exc:
        logger.error("EmailNotifier thread failed: %s", exc, exc_info=True)
        # fall-through to direct send

    # Direct send (same logic as EmailNotifier.send_notification)
    email_cfg = load_email_config_from_file()
    required = [email_cfg.get("smtp_host"), email_cfg.get("smtp_port"), email_cfg.get("recipients")]
    if not all(required):
        raise HTTPException(status_code=500, detail="Email settings are incomplete")

    recipients = [e.strip() for e in email_cfg.get("recipients", "").split(',') if e.strip()]
    smtp_host = email_cfg.get("smtp_host")
    smtp_port = int(email_cfg.get("smtp_port", 587))
    smtp_user = email_cfg.get("smtp_user") or f"noreply@{smtp_host}"
    smtp_password = email_cfg.get("smtp_password")

    host_name = trigger.get("hosts")[0]["host"] if trigger.get("hosts") else "Unknown Host"
    subject = f"PROBLEM: {trigger['description']} on {host_name}"
    body = f"""
Problem Detected:\n\nHost: {host_name}\nProblem: {trigger['description']}\nSeverity: {trigger['priority']}\n""".strip()

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipients, msg.as_string())
    except Exception as exc:
        logger.error("Direct email send failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send email: {exc}")

    return {"status": "email_sent_direct"}

@app.post("/api/remediate")
def remediate(request: RemediationRequest, zabbix_api: ZabbixAPI = Depends(get_zabbix_api)):
    """Executes a remediation script on a host."""
    try:
        result = zabbix_api.execute_script(script_id=request.script_id, host_id=request.host_id)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hosts/status", response_model=List[HostStatus])
async def get_hosts_status():
    """Get status of all monitored hosts using Zabbix API."""
    api = ZabbixAPI()
    try:
        api.login()
        hosts_raw = api.host_get()  # returns list of {hostid, host}
    except Exception as exc:
        # Fallback to previous mock behaviour if Zabbix is unreachable
        logger.error(f"Failed to fetch hosts from Zabbix: {exc}")
        hosts_raw = [{"hostid": "unknown", "host": "Unknown"}]

    hosts_status: List[HostStatus] = []
    now = datetime.utcnow()
    for h in hosts_raw:
        hosts_status.append(
            HostStatus(
                host_id=h["hostid"],
                name=h.get("name") or h.get("host", h["hostid"]),
                status="up",  # Basic status; could be refined via host.get availability
                last_check=now,
                issues=[],
            )
        )
    return hosts_status

@app.get("/api/hosts/metrics-keys", response_model=List[HostKeys])
async def get_hosts_metric_keys():
    """Return list of hosts with the metric keys available in the *metrics* table."""
    from sqlalchemy import select  # local import to avoid circular deps
    from database import engine, metrics_table

    stmt = select(metrics_table.c.host_id, metrics_table.c.item_key).distinct()

    mapping: dict[str, set[str]] = {}
    with engine.begin() as conn:
        for host_id, item_key in conn.execute(stmt):
            mapping.setdefault(host_id, set()).add(item_key)

    return [HostKeys(host_id=h, keys=sorted(ks)) for h, ks in mapping.items()]

@app.get("/api/alerts", response_model=List[Alert])
def get_alerts():
    api = ZabbixAPI()
    api.login()
    triggers = api.problem_get()  # This method now calls trigger.get

    response = []
    for t in triggers:
        if not t.get("hosts"):
            continue
        response.append(
            Alert(
                id=t["triggerid"],
                host=t["hosts"][0]["host"],
                hostid=t["hosts"][0]["hostid"],
                name=t["description"],
                severity=int(t["priority"]),
            )
        )
    return response

@app.get("/api/metrics/{host_id}", response_model=List[NetworkMetrics])
async def get_host_metrics(host_id: str, hours: int = 24):
    """Return recent metrics for a host (default last *hours* hours)."""
    from sqlalchemy import select, and_, func  # local import to avoid circular deps
    from database import engine, metrics_table

    since = datetime.utcnow() - timedelta(hours=hours)

    stmt = (
        select(
            metrics_table.c.timestamp,
            metrics_table.c.item_key,
            metrics_table.c.value,
        )
        .where(
            and_(
                metrics_table.c.host_id == host_id,
                metrics_table.c.timestamp >= since,
            )
        )
        .order_by(metrics_table.c.timestamp)
    )

    cpu_key = "system.cpu.util"
    mem_key = "vm.memory.size[available]"
    mem_total_key = "vm.memory.size[total]"

    # Build mapping {timestamp -> {item_key: value}}
    buckets: dict[Any, dict[str, float]] = {}
    with engine.begin() as conn:
        for ts, key, val in conn.execute(stmt):
            buckets.setdefault(ts, {})[key] = float(val)

    response: List[NetworkMetrics] = []
    for ts in sorted(buckets.keys()):
        data = buckets[ts]



        # Find network keys dynamically
        net_in_value = 0.0
        net_out_value = 0.0
        for key, value in data.items():
            if key.startswith('net.if.in'):
                net_in_value = value
            elif key.startswith('net.if.out'):
                net_out_value = value

        response.append(
            NetworkMetrics(
                timestamp=ts,
                host_id=host_id,
                cpu_usage=data.get(cpu_key, 0.0),
                memory_usage=data.get(mem_key, 0.0),
                memory_total=data.get(mem_total_key),
                network_in=net_in_value,
                network_out=net_out_value,
            )
        )
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
