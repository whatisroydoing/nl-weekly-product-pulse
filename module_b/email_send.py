"""
B2 — Email Send (smtplib + Gmail)
Sends pulse summary as a formatted HTML email to up to 5 recipients.
Optionally attaches the PDF if a path is provided.
"""

import os
import smtplib
import ssl
import logging
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from models.schemas import PulsePayload

load_dotenv(override=True)
logger = logging.getLogger(__name__)


def _build_html(pulse: PulsePayload) -> str:
    """Build a clean HTML email body from the PulsePayload."""
    app_name  = pulse.metadata.get("app_name", "IndMoney")
    date_str  = pulse.metadata.get("generated_at", datetime.now().strftime("%d-%b-%Y"))
    reviews   = pulse.metadata.get("review_count", "N/A")
    source    = pulse.metadata.get("source", "Google Play Store")

    # Themes rows
    theme_rows = ""
    for t in pulse.themes:
        star  = "★ " if t.is_top_3 else ""
        bold  = "font-weight:bold;" if t.is_top_3 else ""
        theme_rows += (
            f"<tr>"
            f"<td style='padding:6px 10px;{bold}'>{star}{t.label}</td>"
            f"<td style='padding:6px 10px;text-align:center;'>{t.review_count}</td>"
            f"</tr>"
        )

    # Action items
    action_html = ""
    for item in pulse.action_items:
        action_html += (
            f"<div style='margin-bottom:12px;'>"
            f"<b style='color:#1A3C6E;'>[{item.id}] {item.title}</b><br/>"
            f"<span style='color:#333;'>{item.description}</span>"
            f"</div>"
        )
        
    # Fee Explainer (Optional)
    fee_html = ""
    if hasattr(pulse, '_fee_explainer') and pulse._fee_explainer:
        fee = pulse._fee_explainer
        bullets_html = "".join([f"<li style='margin-bottom:6px;'>{b}</li>" for b in fee.bullets])
        sources_html = "".join([f"<li><a href='{s}' style='color:#1A3C6E;'>{s}</a></li>" for s in fee.source_links])
        
        fee_html = f"""
        <!-- Fee Explainer -->
        <h2 style="color:#1A3C6E;font-size:15px;margin-top:24px;">Fee Scenario: {fee.scenario}</h2>
        <div style="background:#f4f7fa;padding:16px;border-radius:6px;border:1px solid #e1e8f0;">
          <ul style="margin-top:0;padding-left:20px;">
            {bullets_html}
          </ul>
          <p style="margin-top:12px;margin-bottom:4px;font-weight:bold;font-size:12px;color:#555;">Sources:</p>
          <ul style="margin-top:0;padding-left:20px;font-size:12px;color:#555;word-break:break-all;">
            {sources_html}
          </ul>
          <p style="margin-top:12px;margin-bottom:0;font-size:11px;color:#888;">
            Last checked: {fee.last_checked}
          </p>
        </div>
        """

    formatted_summary = pulse.summary_note.replace('\n', '<br>')

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;color:#1A1A1A;max-width:640px;margin:auto;">

  <!-- Header -->
  <div style="background:#1A3C6E;padding:20px 24px;border-radius:6px 6px 0 0;">
    <h1 style="color:white;margin:0;font-size:20px;">{app_name} — Weekly Product Pulse</h1>
    <p style="color:#aac4e8;margin:4px 0 0;font-size:13px;">
      {source} &nbsp;·&nbsp; {reviews} reviews &nbsp;·&nbsp; {date_str}
    </p>
  </div>

  <!-- Orange bar -->
  <div style="background:#F4801A;height:4px;"></div>

  <div style="padding:24px;">

    <!-- Summary -->
    <h2 style="color:#1A3C6E;font-size:15px;margin-top:0;">Summary</h2>
    <p style="line-height:1.6;">{formatted_summary}</p>

    <!-- Themes -->
    <h2 style="color:#1A3C6E;font-size:15px;">Themes</h2>
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;font-size:13px;">
      <thead>
        <tr style="background:#1A3C6E;color:white;">
          <th style="padding:8px 10px;text-align:left;">Theme</th>
          <th style="padding:8px 10px;text-align:center;">Reviews</th>
        </tr>
      </thead>
      <tbody>{theme_rows}</tbody>
    </table>

    <!-- Action Items -->
    <h2 style="color:#1A3C6E;font-size:15px;margin-top:24px;">Action Items</h2>
    {action_html}

    {fee_html}

    <!-- Footer -->
    <hr style="border:none;border-top:1px solid #ddd;margin:24px 0 12px;">
    <p style="color:#888;font-size:11px;text-align:center;">
      {pulse.footer}
    </p>

  </div>
</body>
</html>
"""

def _get_gmail_service():
    """Helper to build the Gmail API service using OAuth2 or Service Account."""
    mode = os.environ.get("GMAIL_API_AUTH_MODE", "SERVICE_ACCOUNT").upper()
    
    if mode == "OAUTH2":
        # Personal Account via Refresh Token (Best for @gmail.com)
        creds = Credentials(
            token=None,
            refresh_token=os.environ.get("GMAIL_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ.get("GMAIL_CLIENT_ID"),
            client_secret=os.environ.get("GMAIL_CLIENT_SECRET"),
            scopes=["https://www.googleapis.com/auth/gmail.send"]
        )
        if not creds.refresh_token:
            logger.error("GMAIL_REFRESH_TOKEN is missing for OAUTH2 mode.")
            return None
        creds.refresh(Request())
        return build("gmail", "v1", credentials=creds)
    
    else:
        # Service Account with Domain-Wide Delegation (Workspace only)
        sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        delegate_user = os.environ.get("GMAIL_DELEGATE_USER")
        
        if not sa_json or not delegate_user:
            logger.error("GOOGLE_SERVICE_ACCOUNT_JSON or GMAIL_DELEGATE_USER missing for SERVICE_ACCOUNT mode.")
            return None
            
        scopes = ["https://www.googleapis.com/auth/gmail.send"]
        
        try:
            import json
            # Robust check for sa_json
            sa_json_clean = (sa_json or "").strip()
            if not sa_json_clean:
                logger.error("GOOGLE_SERVICE_ACCOUNT_JSON is empty for SERVICE_ACCOUNT mode.")
                return None
                
            if sa_json_clean.startswith("{"):
                info = json.loads(sa_json_clean)
                creds = service_account.Credentials.from_service_account_info(
                    info, scopes=scopes
                ).with_subject(delegate_user)
            else:
                creds = service_account.Credentials.from_service_account_file(
                    sa_json_clean, scopes=scopes
                ).with_subject(delegate_user)
                
            return build("gmail", "v1", credentials=creds)
        except Exception as e:
            logger.error(f"Failed to build Gmail service with Service Account: {e}")
            return None

def send_email_via_api(msg: MIMEMultipart, recipients: list) -> dict:
    """Send email using GMAIL API."""
    try:
        service = _get_gmail_service()
        if not service:
            return {"success": False, "error": "Could not initialize Gmail API service. Check settings."}
            
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        create_message = {'raw': raw_message}
        
        service.users().messages().send(userId="me", body=create_message).execute()
        return {"success": True}
    except Exception as e:
        logger.error(f"Gmail API send failed: {e}")
        return {"success": False, "error": f"Gmail API Error: {str(e)}"}


def send_email(
    pulse: PulsePayload,
    recipients: list[str],
    pdf_path: str = "",
    fee_explainer = None,
) -> dict:
    """
    Send a formatted HTML pulse email via Gmail SMTP.

    Reads GMAIL_USER and GMAIL_APP_PASSWORD from .env.
    Optionally attaches a PDF if pdf_path is provided.

    Args:
        pulse: PulsePayload to send.
        recipients: List of email addresses (max 5).
        pdf_path: Optional path to a PDF attachment.
        fee_explainer: Optional FeeExplainerResult to include in the email body.

    Returns:
        dict with keys: success (bool), error (str, optional).
    """
    # Validate
    if not recipients:
        return {"success": False, "error": "At least one recipient required."}
    if len(recipients) > 5:
        return {"success": False, "error": "Maximum 5 recipients allowed."}

    gmail_user     = os.environ.get("GMAIL_USER", "")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "")
    email_mode     = os.environ.get("EMAIL_MODE", "API").upper()

    if not gmail_user:
        return {"success": False, "error": "GMAIL_USER not set in .env."}
    
    # Only require APP_PASSWORD if using SMTP
    if email_mode != "API" and not gmail_password:
        return {"success": False, "error": "GMAIL_APP_PASSWORD not set in .env (Required for SMTP mode)."}

    app_name = pulse.metadata.get("app_name", "IndMoney")
    date_str = pulse.metadata.get("generated_at", datetime.now().strftime("%d-%b-%Y"))
    subject  = f"{app_name} — Weekly Product Pulse ({date_str})"

    # Build message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"IndMoney Product Pulse <{gmail_user}>"
    msg["To"]      = ", ".join(recipients)

    # Temporarily attach fee_explainer to pulse so _build_html can find it
    if fee_explainer:
        pulse._fee_explainer = fee_explainer
    
    msg.attach(MIMEText(_build_html(pulse), "html"))

    # Cleanup temporary attribute
    if fee_explainer:
        delattr(pulse, '_fee_explainer')

    # Attach PDF if provided
    if pdf_path and Path(pdf_path).exists():
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={Path(pdf_path).name}",
        )
        msg.attach(part)

    # Trigger switch between SMTP and API (default: API for Railway compatibility)
    mode = os.environ.get("EMAIL_MODE", "API").upper()
    
    if mode == "API":
        return send_email_via_api(msg, recipients)

    # Fallback to SMTP
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    try:
        context = ssl.create_default_context()
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                server.login(gmail_user, gmail_password)
                server.sendmail(gmail_user, recipients, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(gmail_user, gmail_password)
                server.sendmail(gmail_user, recipients, msg.as_string())
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": f"SMTP Error: {str(e)} (Ensure GMAIL_APP_PASSWORD is correct or switch to EMAIL_MODE=API)"}
