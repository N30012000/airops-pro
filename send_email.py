import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration from your prompt
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "zuberinoosha1@gmail.com"  # Replace with your actual Gmail
SMTP_PASSWORD = "abcd efgh ijkl mnop"   # Replace with the 16-digit App Password (spaces are fine)

def send_test_email():
    try:
        # 1. Create the email content
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = SMTP_USERNAME  # Sending to yourself for testing
        msg['Subject'] = "Test Email from Python"
        
        body = "This is a test email sent using Gmail SMTP and an App Password."
        msg.attach(MIMEText(body, 'plain'))

        # 2. Connect to the Gmail Server
        print("Connecting to server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        
        # 3. Secure the connection (TLS)
        server.starttls()
        
        # 4. Login
        print("Logging in...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # 5. Send the email
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, SMTP_USERNAME, text)
        print("✅ Email sent successfully!")
        
        # 6. Close connection
        server.quit()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_test_email()
