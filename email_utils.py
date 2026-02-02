"""
Email Utilities Module for Air Sial SMS v3.0
Handles SMTP email sending and logging
"""

import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

class SMTPClient:
    """SMTP Email Client for sending safety notifications"""
    
    def __init__(self, server, port, username, password, use_tls=True):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.connection = None
        self.email_logs = []
    
    def connect(self):
        """Establish SMTP connection"""
        try:
            if self.use_tls:
                self.connection = smtplib.SMTP(self.server, self.port)
                self.connection.starttls()
            else:
                self.connection = smtplib.SMTP_SSL(self.server, self.port)
            
            self.connection.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"❌ SMTP Connection Failed: {e}")
            return False
    
    def send_email(self, report_id, subject, body, recipients, attachments=None, high_priority=False):
        """
        Send email via SMTP
        
        Args:
            report_id: Safety report ID for logging
            subject: Email subject
            body: Email body (plain text)
            recipients: List of recipient emails
            attachments: List of file paths to attach
            high_priority: Mark as high priority
        
        Returns:
            dict: {status: "sent"|"failed", message: str}
        """
        try:
            # Ensure recipients is a list
            if isinstance(recipients, str):
                recipients = [recipients]
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = st.secrets.get("SMTP_USERNAME", "noreply@airsial.com")
            msg['To'] = ", ".join(recipients)
            
            if high_priority:
                msg['X-Priority'] = '1'
                msg['Importance'] = 'high'
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect if not already connected
            if not self.connection:
                if not self.connect():
                    return {"status": "failed", "message": "Could not connect to SMTP server"}
            
            # Send email
            self.connection.sendmail(
                msg['From'],
                recipients,
                msg.as_string()
            )
            
            # Log email
            self.log_email('outbound', report_id, subject, body, recipients, 'sent')
            
            return {"status": "sent", "message": f"Email sent to {len(recipients)} recipient(s)"}
            
        except Exception as e:
            error_msg = f"Email send failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.log_email('outbound', report_id, subject, body, recipients, 'failed', str(e))
            return {"status": "failed", "message": error_msg}
    
    def disconnect(self):
        """Close SMTP connection"""
        if self.connection:
            self.connection.quit()
            self.connection = None
    
    def log_email(self, direction, report_id, subject, body, recipients, status, error=None):
        """Log email for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'direction': direction,  # 'outbound' or 'inbound'
            'report_id': report_id,
            'subject': subject,
            'body': body[:500],  # First 500 chars
            'recipients': recipients if isinstance(recipients, list) else [recipients],
            'status': status,
            'error': error
        }
        self.email_logs.append(log_entry)
        return log_entry
    
    def log_reply(self, report_id, sender, message):
        """Log incoming reply"""
        return self.log_email('inbound', report_id, f"Reply: {message[:50]}", message, sender, 'received')
    
    def get_email_logs(self, report_id=None):
        """Retrieve email logs (optionally filtered by report_id)"""
        if report_id:
            return [e for e in self.email_logs if e['report_id'] == report_id]
        return self.email_logs


# Global email functions for convenience
def send_email(to_address, cc_address, subject, body, attachments=None, high_priority=False, report_id=None):
    """
    Convenience function to send email
    Uses credentials from Streamlit secrets
    """
    try:
        smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("SMTP_PORT", 587))
        smtp_user = st.secrets.get("SMTP_USERNAME", "")
        smtp_pass = st.secrets.get("SMTP_PASSWORD", "")
        
        if not smtp_user or not smtp_pass:
            print("⚠️ SMTP credentials not configured in secrets")
            return False
        
        client = SMTPClient(smtp_server, smtp_port, smtp_user, smtp_pass)
        
        recipients = [to_address]
        if cc_address:
            recipients.append(cc_address)
        
        result = client.send_email(
            report_id or "SYSTEM",
            subject,
            body,
            recipients,
            attachments,
            high_priority
        )
        
        client.disconnect()
        return result['status'] == 'sent'
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def get_email_logs(report_id=None):
    """
    Retrieve email logs from session state or return mock data
    """
    if 'email_logs' not in st.session_state:
        st.session_state['email_logs'] = []
    
    logs = st.session_state['email_logs']
    
    if report_id:
        return [e for e in logs if e.get('report_id') == report_id]
    
    return logs


def log_email_to_session(direction, report_id, subject, body, sender, status='sent'):
    """Log email to session state"""
    if 'email_logs' not in st.session_state:
        st.session_state['email_logs'] = []
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'direction': direction,
        'report_id': report_id,
        'subject': subject,
        'body': body[:200],
        'sender': sender,
        'status': status
    }
    
    st.session_state['email_logs'].append(log_entry)
    return log_entry


def get_unique_report_ids_with_emails():
    """Get list of unique report IDs that have email communications"""
    if 'email_logs' not in st.session_state:
        return []
    
    logs = st.session_state['email_logs']
    report_ids = set(e.get('report_id') for e in logs if e.get('report_id'))
    
    return list(report_ids)
