"""Communication commands for Arya.

Email credentials and saved recipients deliberately live outside source code.
"""

import json
import os
import smtplib
import ssl
import webbrowser
from email.message import EmailMessage
from pathlib import Path

from commands.media import send_whatsapp


EMAIL_CONTACTS_FILE = Path(__file__).resolve().parents[1] / "data" / "email_contacts.json"


def _email_contacts():
    if not EMAIL_CONTACTS_FILE.exists():
        return {}
    try:
        saved = json.loads(EMAIL_CONTACTS_FILE.read_text(encoding="utf-8"))
        return {str(name).casefold(): str(address) for name, address in saved.items()}
    except (OSError, json.JSONDecodeError):
        return {}


def _recipient_address(recipient):
    recipient = (recipient or "").strip()
    if "@" in recipient:
        return recipient
    return _email_contacts().get(recipient.casefold())


def send_email(recipient=None, subject=None, body=None, confirmed=False):
    """Send an SMTP email after the application collects final user confirmation."""
    address = _recipient_address(recipient)
    if not address:
        return {"success": False, "message": "No email address found. Use an email address or add the contact to data/email_contacts.json."}
    if not (subject or "").strip() or not (body or "").strip():
        return {"success": False, "message": "An email needs both a subject and a message body."}
    if not confirmed:
        return {"success": False, "message": "Email is ready but needs your confirmation before sending."}

    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    port = int(os.getenv("SMTP_PORT", "465"))
    if not all((host, username, password)):
        return {"success": False, "message": "Email is not configured. Add SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD to .env."}

    email = EmailMessage()
    email["From"] = username
    email["To"] = address
    email["Subject"] = subject.strip()
    email.set_content(body.strip())
    try:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=20) as server:
            server.login(username, password)
            server.send_message(email)
        return {"success": True, "message": f"Email sent to {recipient or address}."}
    except (OSError, smtplib.SMTPException) as error:
        return {"success": False, "message": f"Could not send email: {error}"}


def open_telegram():
    webbrowser.open_new_tab("https://web.telegram.org/")
    return {"success": True, "message": "Opening Telegram Web."}


def open_meet():
    webbrowser.open_new_tab("https://meet.google.com/")
    return {"success": True, "message": "Opening Google Meet."}


def arrange_a_meeting_on_meet():
    """Open Google's new-meeting page; creating/scheduling needs the signed-in account."""
    webbrowser.open_new_tab("https://meet.google.com/new")
    return {"success": True, "message": "Opening a new Google Meet. Choose your meeting options in the browser."}


def open_zoom():
    webbrowser.open_new_tab("https://app.zoom.us/wc/")
    return {"success": True, "message": "Opening Zoom."}
