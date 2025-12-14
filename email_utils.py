# email_utils.py
import smtplib
import sqlite3
import json
from email.message import EmailMessage
from datetime import datetime
from typing import List, Optional, Dict
import os

# Create DB in a persistent location if possible, or local
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
        sender TEXT,
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

def log_email(direction, report_id, sender, subject, body, recipients, status, smtp_response=""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = _conn.cursor()
    cur.execute(
        "INSERT INTO emails (timestamp, direction, report_id, sender, subject, body, recipients, status, smtp_response) VALUES (?,?,?,?,?,?,?,?,?)",
        (ts, direction, report_id, sender, subject, body, json.dumps(recipients), status, smtp_response)
    )
    _conn.commit()
    return cur.lastrowid

def get_email_logs(report_id=None, limit=500):
    cur = _conn.cursor()
    if report_id:
        cur.execute("SELECT * FROM emails WHERE report_id = ? ORDER BY id ASC", (str(report_id),))
    else:
        cur.execute("SELECT * FROM emails ORDER BY id DESC LIMIT ?", (limit,))
    
    rows = cur.fetchall()
    keys = ["id","timestamp","direction","report_id","sender","subject","body","recipients","status","smtp_response"]
    return [dict(zip(keys,row)) for row in rows]

def get_unique_report_ids_with_emails():
    cur = _conn.cursor()
    cur.execute("SELECT DISTINCT report_id FROM emails WHERE report_id IS NOT NULL AND report_id != ''")
    return [row[0] for row in cur.fetchall()]

class SMTPClient:
    def __init__(self, host, port, username, password, use_tls=True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def send_email(self, report_id, subject, body, recipients, attachments=None):
        msg = EmailMessage()
        msg["From"] = self.username
        msg["To"] = ", ".join(recipients) if isinstance(recipients, list) else recipients
        msg["Subject"] = subject
        msg.set_content(body)

        if attachments:
            for att in attachments:
                # Basic attachment handling - assumes tuple (filename, content_bytes, type)
                try:
                    msg.add_attachment(att[1], maintype='application', subtype='octet-stream', filename=att[0])
                except:
                    pass

        status = "failed"
        response = ""
        
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.host, self.port)
            
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            status = "sent"
            response = "250 OK"
        except Exception as e:
            response = str(e)
            print(f"SMTP Error: {e}")

        # Log the OUTGOING email
        log_email("outbound", report_id, self.username, subject, body, recipients, status, response)
        return status == "sent"

    def log_reply(self, report_id, sender, body):
        """Manually log an incoming reply for the chat view"""
        log_email("inbound", report_id, sender, f"Re: Report {report_id}", body, [self.username], "received", "manual_entry")
        return True
