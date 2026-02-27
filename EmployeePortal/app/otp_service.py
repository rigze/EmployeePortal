"""
OTP Service using Gmail SMTP
Sends OTP codes via email for free — no API costs.
"""
import smtplib
import os
import random
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

log = logging.getLogger("otp_service")

# Load .env file
load_dotenv()

# Gmail SMTP configuration
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")       # Your Gmail address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Gmail App Password (NOT your regular password)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP"""
    return str(random.randint(10**(length-1), 10**length - 1))


async def send_otp_email(to_email: str, otp_code: str, employee_id: str = "") -> dict:
    """
    Send OTP via email using Gmail SMTP.
    
    Args:
        to_email: Recipient email address
        otp_code: The OTP to send
        employee_id: Employee ID for the email subject
    
    Returns:
        dict with 'success' (bool) and 'message' (str)
    """
    # Validate email
    if not to_email or "@" not in to_email:
        log.warning(f"No valid email for {employee_id}, falling back to console")
        return {"success": True, "message": "No email configured, OTP printed to console", "fallback": True}
    
    # Check if SMTP is configured
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        log.warning("SMTP not configured, OTP returned in API response")
        return {"success": True, "message": "SMTP not configured, OTP printed to console", "fallback": True}
    
    try:
        # Create email message
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg["Subject"] = f"Employee Portal - OTP Verification"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 400px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; padding: 30px;">
                <h2 style="color: #333; text-align: center;">🔐 OTP Verification</h2>
                <p style="color: #555;">Your One-Time Password for Employee Portal login:</p>
                <div style="background: #f5f5f5; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #2196F3;">{otp_code}</span>
                </div>
                <p style="color: #888; font-size: 13px;">
                    ⏱ This OTP is valid for <strong>5 minutes</strong>.<br>
                    ⚠ Do not share this code with anyone.
                </p>
                <hr style="border: none; border-top: 1px solid #eee;">
                <p style="color: #aaa; font-size: 11px; text-align: center;">
                    Government of Sikkim - Employee Portal
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        
        log.info(f"OTP email sent to {to_email}")
        return {"success": True, "message": "OTP sent to your email"}
        
    except Exception as e:
        log.error(f"Email sending failed: {e}")
        return {"success": True, "message": f"Email error ({str(e)}), OTP printed to console", "fallback": True}
