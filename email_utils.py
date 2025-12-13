# email_utils.py
# SMTP client, templates, and local SQLite email log
import smtplib
import sqlite3
import json
from email.message import EmailMessage
from datetime import datetime
from typing import List, Optional, Dict
from config_loader import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD

DB_PATH = "email_logs.db"

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        direction TEXT,
        report_id TEXT,
        subject TEXT,
        body TEXT,
        recipients TEXT,
        status TEXT,
        smtp_response TEXT
    )
    """)
    conn.commit()
    return conn

_conn = init_db()

EMAIL_TEMPLATES = {
    "incident_report": {
        "subject": "Air Sial Incident Report - {report_id}",
        "body": "Dear {recipient_name},\n\nPlease find the incident report {report_id} attached.\n\nSummary:\n{summary}\n\nRegards,\nAir Sial Safety Team"
    },
    "ramp_inspection": {
        "subject": "Ramp Inspection Report - {report_id}",
        "body": "Dear {recipient_name},\n\nRamp inspection {report_id} details:\n{summary}\n\nRegards,\nAir Sial Safety Team"
    },
    "generic": {
        "subject": "{subject}",
        "body": "{body}"
    }
}

def log_email(direction, report_id, subject, body, recipients, status, smtp_response=""):
    ts = datetime.utcnow().isoformat()
    cur = _conn.cursor()
    cur.execute(
        "INSERT INTO emails (timestamp,direction,report_id,subject,body,recipients,status,smtp_response) VALUES (?,?,?,?,?,?,?,?)",
        (ts, direction, report_id, subject, body, json.dumps(recipients), status, smtp_response)
    )
    _conn.commit()
    return cur.lastrowid

def get_email_logs(limit=200):
    cur = _conn.cursor()
    cur.execute("SELECT id,timestamp,direction,report_id,subject,body,recipients,status,smtp_response FROM emails ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    keys = ["id","timestamp","direction","report_id","subject","body","recipients","status","smtp_response"]
    return [dict(zip(keys,row)) for row in rows]

class SMTPClient:
    def __init__(self, host=None, port=None, username=None, password=None, use_tls=True):
        self.host = host or SMTP_SERVER
        self.port = port or SMTP_PORT
        self.username = username or SMTP_USERNAME
        self.password = password or SMTP_PASSWORD
        self.use_tls = use_tls

    def send_email(self, subject: str, body: str, recipients: List[str], attachments: Optional[List[Dict]] = None, report_id: Optional[str] = None):
        msg = EmailMessage()
        msg["From"] = self.username
        msg["To"] = ", ".join(recipients) if isinstance(recipients, (list,tuple)) else recipients
        msg["Subject"] = subject
        msg.set_content(body)

        if attachments:
            for att in attachments:
                msg.add_attachment(att["content"], maintype=att.get("maintype","application"), subtype=att.get("subtype","octet-stream"), filename=att["filename"])

        try:
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port, timeout=20)
                server.ehlo()
                server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
            else:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=20)
                if self.username and self.password:
                    server.login(self.username, self.password)

            resp = server.send_message(msg)
            server.quit()
            status = "sent"
            smtp_response = str(resp)
        except Exception as e:
            status = "failed"
            smtp_response = str(e)

        log_email("sent", report_id or "", subject, body, recipients, status, smtp_response)
        return {"status": status, "smtp_response": smtp_response}

def render_template(template_key: str, **kwargs):
    tpl = EMAIL_TEMPLATES.get(template_key, EMAIL_TEMPLATES["generic"])
    subject = tpl["subject"].format(**kwargs)
    body = tpl["body"].format(**kwargs)
    return subject, body
