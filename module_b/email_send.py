"""
B2 — Email Send (smtplib + Gmail)
Sends pulse summary as a formatted HTML email to up to 5 recipients.
Optionally attaches the PDF if a path is provided.
"""

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from models.schemas import PulsePayload

load_dotenv()


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

    if not gmail_user or not gmail_password:
        return {"success": False, "error": "GMAIL_USER or GMAIL_APP_PASSWORD not set in .env."}

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

    # Send via Gmail SMTP TLS
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipients, msg.as_string())
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
