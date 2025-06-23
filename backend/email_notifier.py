import os
import smtplib
import time
from email.mime.text import MIMEText
from threading import Thread
from typing import Dict

from collector import ZabbixAPI

class EmailNotifier(Thread):
    def __init__(
        self,
        smtp_host,
        smtp_port,
        smtp_user,
        smtp_password,
        recipients,
        interval_seconds=60,
    ):
        super().__init__()
        self.daemon = True
        self.interval_seconds = interval_seconds
        self.active_triggers: Dict[str, Dict] = {}

        # Store email config
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.recipients = recipients

    def run(self):
        # Wait a bit for services to be ready
        print("[EmailNotifier] Starting up, waiting 30s...")
        time.sleep(30)
        print("[EmailNotifier] Service started.")

        while True:
            try:
                self.check_and_notify()
            except Exception as e:
                print(f"[EmailNotifier] Error during check cycle: {e}")
            time.sleep(self.interval_seconds)

    def check_and_notify(self):
        api = ZabbixAPI()
        api.login()

        # This method gets active triggers (value=1)
        current_triggers_list = api.problem_get()
        current_triggers_map = {t["triggerid"]: t for t in current_triggers_list}

        current_ids = set(current_triggers_map.keys())
        previous_ids = set(self.active_triggers.keys())

        # Identify new problems
        new_ids = current_ids - previous_ids
        for trigger_id in new_ids:
            trigger = current_triggers_map[trigger_id]
            self.send_notification(trigger, "PROBLEM")

        # Identify resolved problems
        resolved_ids = previous_ids - current_ids
        for trigger_id in resolved_ids:
            trigger = self.active_triggers[
                trigger_id
            ]  # Get data from the old state
            self.send_notification(trigger, "OK")

        # Update state for the next cycle
        self.active_triggers = current_triggers_map

    def send_notification(self, trigger, status):
        if not all(
            [
                self.smtp_host,
                self.smtp_port,
                self.smtp_user,
                self.smtp_password,
                self.recipients,
            ]
        ):
            print(
                "[EmailNotifier] Email settings are not fully configured. Skipping notification."
            )
            return

        host_name = (
            trigger.get("hosts")[0]["host"] if trigger.get("hosts") else "Unknown Host"
        )

        if status == "PROBLEM":
            subject = f"PROBLEM: {trigger['description']} on {host_name}"
            body = f"""
Problem Detected:

Host: {host_name}
Problem: {trigger['description']}
Severity: {trigger['priority']}

Please investigate the issue.
"""
        elif status == "OK":
            subject = f"RESOLVED: {trigger['description']} on {host_name}"
            body = f"""
Problem Resolved:

Host: {host_name}
Problem: {trigger['description']}

This issue has been resolved.
"""
        else:
            return  # Should not happen

        msg = MIMEText(body.strip())
        msg["Subject"] = subject
        msg["From"] = self.smtp_user
        msg["To"] = ", ".join(self.recipients)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, self.recipients, msg.as_string())
                print(
                    f"[EmailNotifier] Sent '{status}' notification for: {trigger['description']}"
                )
        except Exception as e:
            print(f"[EmailNotifier] Failed to send email: {e}")
