
import json
import re
from pathlib import Path

import pyautogui
import pywhatkit


CONTACTS_FILE = Path(__file__).resolve().parents[1] / "data" / "contacts.json"

def _key(key, message):
    pyautogui.press(key)
    return {"success": True, "message": message}

def play_music():
    return _key("playpause", "Toggled music playback.")

def pause_music():
    return _key("playpause", "Paused music.")

def resume_music():
    return _key("playpause", "Resumed music.")

def stop_song():
    return _key("stop", "Stopped music.")

def next_song():
    return _key("nexttrack", "Playing next track.")

def previous_song():
    return _key("prevtrack", "Playing previous track.")

def volume_up():
    return _key("volumeup", "Volume increased.")

def volume_down():
    return _key("volumedown", "Volume decreased.")

def mute_volume():
    return _key("volumemute", "Volume muted.")


def _normalise_phone(phone):
    """Return an international phone number accepted by WhatsApp, or None."""
    if not phone:
        return None
    digits = re.sub(r"[^0-9+]", "", str(phone))
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    elif not digits.startswith("+"):
        digits = "+" + digits
    return digits if re.fullmatch(r"\+[1-9]\d{7,14}", digits) else None


def _saved_contacts():
    if not CONTACTS_FILE.exists():
        return {}
    try:
        data = json.loads(CONTACTS_FILE.read_text(encoding="utf-8"))
        return {str(name).casefold(): number for name, number in data.items()}
    except (OSError, json.JSONDecodeError):
        return {}


def send_whatsapp(contact=None, message=None, phone=None, confirmed=False):
    """Send one WhatsApp Web message after confirmation from the UI.

    Contacts are resolved from ``data/contacts.json``; values must be international
    phone numbers, e.g. ``{"Sourav": "+919876543210"}``.
    """
    recipient = (contact or "").strip()
    text = (message or "").strip()
    if not recipient and not phone:
        return {"success": False, "message": "Please provide a contact name or phone number."}
    if not text:
        return {"success": False, "message": "Please provide a message to send."}

    saved_number = _saved_contacts().get(recipient.casefold()) if recipient else None
    number = _normalise_phone(phone or saved_number or recipient)
    if not number:
        return {
            "success": False,
            "message": f"No valid number is saved for {recipient}. Add it to data/contacts.json using international format.",
        }
    if not confirmed:
        return {"success": False, "message": "Message is ready but needs your confirmation before sending."}

    try:
        # WhatsApp Web opens, waits for it to load, then sends the prepared text.
        pywhatkit.sendwhatmsg_instantly(number, text, wait_time=15, tab_close=True, close_time=3)
        label = recipient or number
        return {"success": True, "message": f"Message sent to {label}."}
    except Exception as error:
        return {"success": False, "message": f"Could not send WhatsApp message: {error}"}

