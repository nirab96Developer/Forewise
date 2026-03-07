"""Email utilities - supports both SMTP and HTTP API (SendGrid/Brevo)"""

import smtplib
import requests
import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from typing import Optional, List, Tuple
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

# Load .env file (override=True to ensure values are set even if env was clean)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

from app.core.config import settings

# Cache the API key at module load time (after load_dotenv)
_BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")

def get_brevo_api_key():
    """Get Brevo API key from environment"""
    return _BREVO_API_KEY or os.getenv("BREVO_API_KEY", "")

def get_sendgrid_api_key():
    """Get SendGrid API key from environment"""
    return os.getenv("SENDGRID_API_KEY", "")


def send_via_sendgrid(to: str, subject: str, body: str) -> dict:
    """Send email via SendGrid HTTP API"""
    api_key = get_sendgrid_api_key()
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": settings.EMAIL_FROM, "name": settings.EMAIL_FROM_NAME},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}]
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    if response.status_code in [200, 201, 202]:
        logger.info(f"[OK] Email sent via SendGrid to {to}: {subject}")
        return {"message": "Email sent via SendGrid", "recipient": to}
    else:
        raise Exception(f"SendGrid error: {response.status_code} - {response.text}")


def send_via_brevo(
    to: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    attachments: Optional[List[Tuple[str, bytes, str]]] = None
) -> dict:
    """
    Send email via Brevo (Sendinblue) HTTP API

    Args:
        to: Recipient email
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
        attachments: Optional list of (filename, content_bytes, content_type) tuples
    """
    api_key = get_brevo_api_key()
    if not api_key:
        raise Exception("No Brevo API key available")
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "sender": {"name": settings.EMAIL_FROM_NAME, "email": settings.EMAIL_FROM},
        "to": [{"email": to}],
        "subject": subject,
        "textContent": body
    }

    # Add HTML body if provided
    if html_body:
        data["htmlContent"] = html_body

    # Add attachments if provided
    if attachments:
        data["attachment"] = []
        for filename, content, content_type in attachments:
            encoded = base64.b64encode(content).decode('utf-8')
            data["attachment"].append({
                "name": filename,
                "content": encoded,
            })

    response = requests.post(url, headers=headers, json=data, timeout=30)
    if response.status_code in [200, 201, 202]:
        attachment_info = f" with {len(attachments)} attachment(s)" if attachments else ""
        logger.info(f"[OK] Email sent via Brevo to {to}: {subject}{attachment_info}")
        return {"message": "Email sent via Brevo", "recipient": to}
    else:
        raise Exception(f"Brevo error: {response.status_code} - {response.text}")


def send_via_smtp(to: str, subject: str, body: str) -> dict:
    """Send email via SMTP"""
    msg = MIMEMultipart()
    msg['From'] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
    msg['To'] = to
    msg['Subject'] = str(Header(subject, 'utf-8'))
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
    server.starttls()
    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    server.sendmail(settings.EMAIL_FROM, to, msg.as_string())
    server.quit()

    logger.info(f"[OK] Email sent via SMTP to {to}: {subject}")
    return {"message": "Email sent via SMTP", "recipient": to}


def send_email(to=None, subject="", body="", email_to=None, **kwargs):
    """
    Send email - tries multiple methods:
    1. Brevo API (if BREVO_API_KEY configured)
    2. SendGrid API (if SENDGRID_API_KEY configured)
    3. SMTP (direct connection)
    4. Console fallback
    """
    recipient = to or email_to or "unknown"

    # Try Brevo first (if configured)
    brevo_key = get_brevo_api_key()
    if brevo_key:
        try:
            return send_via_brevo(recipient, subject, body)
        except Exception as e:
            logger.warning(f"Brevo failed for {recipient}: {e}")
    else:
        logger.warning(f"No Brevo API key - skipping Brevo for {recipient}")

    # Try SendGrid second (if configured)
    sendgrid_key = get_sendgrid_api_key()
    if sendgrid_key:
        try:
            return send_via_sendgrid(recipient, subject, body)
        except Exception as e:
            logger.warning(f"SendGrid failed for {recipient}: {e}")

    # Try SMTP
    try:
        return send_via_smtp(recipient, subject, body)
    except Exception as e:
        logger.error(f"SMTP failed for {recipient}: {e}")

    # Fallback to console
    logger.error(f"[FALLBACK] All email methods failed for {recipient}: {subject}")
    return {"message": "Email printed to console (all methods failed)", "recipient": recipient}


def send_welcome_email(email, name=None, **kwargs):
    return send_email(to=email, subject="Welcome", body=f"Welcome {name or 'User'}")


def send_reset_password_email(email, token, **kwargs):
    return send_email(to=email, subject="Password Reset", body=f"Token: {token}")


def send_notification_email(to, subject, body, **kwargs):
    return send_email(to=to, subject=subject, body=body)


def send_work_order_notification(email, work_order_id, status=None, **kwargs):
    return send_email(
        to=email, subject=f"Work Order {work_order_id}", body=f"Status: {status}"
    )


def send_report_email(to, report_type, report_data=None, **kwargs):
    return send_email(to=to, subject=f"Report: {report_type}", body=str(report_data))


def send_approval_email(to, item_type, item_id, **kwargs):
    return send_email(to=to, subject=f"Approval: {item_type}", body=f"ID: {item_id}")


def send_invoice(to, invoice_id, amount=0, **kwargs):
    return send_email(to=to, subject=f"Invoice {invoice_id}", body=f"Amount: {amount}")


def send_invoice_email(to, invoice_id, amount=0, **kwargs):
    return send_invoice(to, invoice_id, amount)


def send_alert_email(to, alert_type, message, **kwargs):
    return send_email(to=to, subject=f"Alert: {alert_type}", body=message)


def send_reminder_email(to, reminder_type, details="", **kwargs):
    return send_email(to=to, subject=f"Reminder: {reminder_type}", body=details)


def send_test_email(to, **kwargs):
    return send_email(to=to, subject="Test", body="Test email")


def send_status_update(to, status, **kwargs):
    return send_email(to=to, subject="Status Update", body=status)


def send_error_notification(to, error, **kwargs):
    return send_email(to=to, subject="Error", body=str(error))


def send_confirmation_email(to, action, **kwargs):
    return send_email(to=to, subject="Confirmation", body=action)


def send_verification_email(to, code, **kwargs):
    return send_email(to=to, subject="Verification", body=f"Code: {code}")


def send_email_with_pdf(
    to: str,
    subject: str,
    body: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    html_body: Optional[str] = None,
) -> dict:
    """
    Send email with PDF attachment via Brevo
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Plain text body
        pdf_bytes: PDF content as bytes
        pdf_filename: Filename for the PDF attachment
        html_body: Optional HTML body
    """
    attachments = [(pdf_filename, pdf_bytes, "application/pdf")]
    
    brevo_key = get_brevo_api_key()
    if brevo_key:
        try:
            return send_via_brevo(
                to=to,
                subject=subject,
                body=body,
                html_body=html_body,
                attachments=attachments
            )
        except Exception as e:
            print(f"[ERROR] Failed to send email with PDF: {e}")
            raise
    else:
        raise Exception("No Brevo API key configured for PDF email")


def send_worklog_approval_email(
    to: str,
    worklog_data: dict,
    segments: list,
    recipient_type: str = "supplier",  # supplier, accountant, manager
) -> dict:
    """
    Send worklog approval email with PDF attachment
    
    Args:
        to: Recipient email
        worklog_data: Worklog data dictionary
        segments: List of segment dictionaries
        recipient_type: Type of recipient (affects email content)
    """
    from app.services.pdf_service import generate_worklog_pdf
    
    report_num = worklog_data.get('report_number_formatted', 'WR-2025-000000')
    report_date = worklog_data.get('report_date', '')
    
    # Generate PDF
    pdf_bytes = generate_worklog_pdf(worklog_data, segments)
    pdf_filename = f"worklog_{report_num}_{report_date}.pdf"
    
    # Email subject
    subject = f"🧾 אישור דיווח שעות - {report_num}"
    
    # Email body based on recipient type
    if recipient_type == "supplier":
        body = f"""
שלום רב,

מצורף אישור דיווח שעות מס' {report_num}

פרטי הדיווח:
• תאריך: {report_date}
• פרויקט: {worklog_data.get('project_name', 'N/A')}
• סה"כ שעות: {worklog_data.get('total_hours', 0)}

לעיונך בלבד.

בברכה,
מערכת קק"ל
"""
    elif recipient_type == "accountant":
        body = f"""
שלום רב,

מצורף דיווח שעות לאישור ולטיפול בחשבונית.

פרטי הדיווח:
• מספר דיווח: {report_num}
• תאריך: {report_date}
• ספק: {worklog_data.get('supplier_name', 'N/A')}
• פרויקט: {worklog_data.get('project_name', 'N/A')}
• סוג: {'תקן' if worklog_data.get('is_standard', True) else 'לא-תקן'}
• סה"כ שעות: {worklog_data.get('total_hours', 0)}

{'נימוק חריגה: ' + worklog_data.get('non_standard_reason', '') if not worklog_data.get('is_standard', True) else ''}

בברכה,
מערכת קק"ל
"""
    else:  # manager
        body = f"""
שלום רב,

דיווח שעות אושר.

פרטי הדיווח:
• מספר דיווח: {report_num}
• תאריך: {report_date}
• ספק: {worklog_data.get('supplier_name', 'N/A')}
• פרויקט: {worklog_data.get('project_name', 'N/A')}
• מנהל עבודה: {worklog_data.get('user_name', 'N/A')}
• סה"כ שעות: {worklog_data.get('total_hours', 0)}

בברכה,
מערכת קק"ל
"""
    
    return send_email_with_pdf(
        to=to,
        subject=subject,
        body=body,
        pdf_bytes=pdf_bytes,
        pdf_filename=pdf_filename,
    )
