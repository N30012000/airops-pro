"""
Email Management Utilities for Aviation Safety SMS
Handles SMTP sending, receiving, and logging to Supabase
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import streamlit as st
from supabase import Client

class SMTPClient:
    """SMTP Email Client with Supabase logging"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = True
    
    def send_email(self, report_id: Optional[str], subject: str, body: str, 
                   recipients: List[str], attachments: List = None) -> Dict:
        """
        Send email and log to Supabase
        
        Returns: {'status': 'sent'|'failed', 'message_id': str, 'error': str}
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    try:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename= {attachment.name}')
                        msg.attach(part)
                    except Exception as e:
                        st.warning(f"Could not attach {attachment.name}: {e}")
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            # Log to Supabase
            self._log_email_to_db(report_id, subject, body, recipients, 'sent')
            
            return {
                'status': 'sent',
                'message_id': msg['Message-ID'],
                'error': None
            }
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = "SMTP Authentication Failed. Check username/password."
            self._log_email_to_db(report_id, subject, body, recipients, 'failed', error_msg)
            return {'status': 'failed', 'message_id': None, 'error': error_msg}
        
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {str(e)}"
            self._log_email_to_db(report_id, subject, body, recipients, 'failed', error_msg)
            return {'status': 'failed', 'message_id': None, 'error': error_msg}
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            return {'status': 'failed', 'message_id': None, 'error': error_msg}
    
    def _log_email_to_db(self, report_id: Optional[str], subject: str, body: str,
                        recipients: List[str], status: str, error: Optional[str] = None):
        """Log email to Supabase"""
        try:
            supabase: Client = st.session_state.get('supabase')
            if not supabase:
                return
            
            email_record = {
                'report_id': report_id,
                'subject': subject,
                'body': body[:1000],  # Truncate long bodies
                'recipients': ', '.join(recipients),
                'status': status,
                'direction': 'outbound',
                'timestamp': datetime.now().isoformat(),
                'error_message': error
            }
            
            supabase.table('email_logs').insert(email_record).execute()
            
        except Exception as e:
            st.warning(f"Could not log email to database: {e}")
    
    def log_reply(self, report_id: str, sender: str, message_body: str):
        """Log an incoming reply"""
        try:
            supabase: Client = st.session_state.get('supabase')
            if not supabase:
                return
            
            reply_record = {
                'report_id': report_id,
                'subject': f'RE: Report {report_id}',
                'body': message_body,
                'sender': sender,
                'direction': 'inbound',
                'status': 'received',
                'timestamp': datetime.now().isoformat()
            }
            
            supabase.table('email_logs').insert(reply_record).execute()
            
        except Exception as e:
            st.error(f"Failed to log reply: {e}")


def get_email_logs(report_id: Optional[str] = None) -> List[Dict]:
    """Retrieve email logs from Supabase"""
    try:
        supabase: Client = st.session_state.get('supabase')
        if not supabase:
            return []
        
        if report_id:
            response = supabase.table('email_logs').select('*').eq('report_id', report_id).execute()
        else:
            response = supabase.table('email_logs').select('*').order('timestamp', desc=True).limit(100).execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        st.warning(f"Could not fetch email logs: {e}")
        return []


def get_unique_report_ids_with_emails() -> List[str]:
    """Get list of report IDs that have email communications"""
    try:
        supabase: Client = st.session_state.get('supabase')
        if not supabase:
            return []
        
        response = supabase.table('email_logs').select('DISTINCT report_id').execute()
        return [r['report_id'] for r in response.data if r.get('report_id')]
        
    except Exception as e:
        st.warning(f"Could not fetch report IDs: {e}")
        return []


def send_notification_email(recipient: str, subject: str, body: str, 
                           smtp_config: Optional[Dict] = None) -> bool:
    """
    Convenience function to send a notification email
    """
    if not smtp_config:
        smtp_config = st.session_state.get('email_settings', {})
    
    try:
        client = SMTPClient(
            smtp_config.get('smtp_server', 'smtp.gmail.com'),
            smtp_config.get('smtp_port', 587),
            smtp_config.get('smtp_user'),
            smtp_config.get('smtp_password')
        )
        
        result = client.send_email(None, subject, body, [recipient])
        return result['status'] == 'sent'
        
    except Exception as e:
        st.error(f"Failed to send notification: {e}")
        return False
