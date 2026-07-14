"""Gemini-backed intent detection with validated structured output."""

from pathlib import Path
from typing import Any, Dict, Literal
import re
import sys

# Allow both `python ai/gemini.py` and package imports from the project root.
if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from pydantic import BaseModel, Field

from config import GEMINI_API_KEY, GEMINI_MODEL

try:
    from google import genai
    from google.genai import types
except ImportError:  # The desktop commands remain usable without the optional SDK.
    genai = None
    types = None


IntentName = Literal[
    "open_app", "close_app", "google_search", "youtube_search", "open_website",
    "shutdown", "restart", "lock_pc", "screenshot", "create_folder", "delete_file",
    "play_music", "pause_music", "volume_up", "volume_down", "mute_volume", "send_whatsapp", "chat",
    "send_email", "open_telegram", "open_meet", "arrange_meeting", "open_zoom",
]


class IntentResponse(BaseModel):
    """The only shape that Gemini may return to the command router."""

    intent: IntentName
    params: Dict[str, Any] = Field(default_factory=dict)


SYSTEM_INSTRUCTION = """You classify a single user request for Arya, a Windows desktop assistant.
Choose the one supported action that most directly satisfies the request.
Use chat for conversation, questions, unsupported requests, or uncertain requests.
Extract only the required arguments. Keep the user's words in argument values; do not invent
paths, app names, URLs, or search queries. Destructive computer actions must only be chosen
when the user explicitly asks for them.

Argument rules:
- open_app and close_app: {app: application name}
- google_search and youtube_search: {query: search terms}
- open_website: {url: website address}
- create_folder and delete_file: {path: user-provided path}
- send_whatsapp: {contact: recipient name, message: message body}; never add confirmed
- send_email: {recipient: email/name, subject: subject, body: email body}; never add confirmed
- chat: {message: original user message}
- all other actions: {}"""

PARAM_KEYS = {
    "open_app": {"app"}, "close_app": {"app"}, "google_search": {"query"},
    "youtube_search": {"query"}, "open_website": {"url"},
    "create_folder": {"path"}, "delete_file": {"path"}, "chat": {"message"},
    "send_whatsapp": {"contact", "message", "phone"},
    "send_email": {"recipient", "subject", "body"},
}


def _fallback(command: str) -> dict:
    text = command.strip()
    lower = text.lower()
    cleaned = re.sub(r"^(?:please |can you |could you |would you )+", "", lower).strip()
    cleaned_text = re.sub(r"^(?:please |can you |could you |would you )+", "", text, flags=re.IGNORECASE).strip()
    patterns = [
        (r"^(?:open|launch) (.+)$", "open_app", "app"),
        (r"^(?:close|quit) (.+)$", "close_app", "app"),
        (r"^(?:google )?(?:search(?: for)?|find) (.+)$", "google_search", "query"),
        (r"^(?:youtube )?(?:search(?: for)?|play) (.+)$", "youtube_search", "query"),
        (r"^(?:open )?(https?://\S+|www\.\S+)$", "open_website", "url"),
        (r"^(?:create|make) (?:a )?folder (.+)$", "create_folder", "path"),
        (r"^delete (?:the )?file (.+)$", "delete_file", "path"),
        (r"^(?:send (?:a )?(?:whatsapp )?message to) (.+?) (?:that|saying) (.+)$", "send_whatsapp", None),
        (r"^send (?:an )?email to (.+?) (?:with )?subject (.+?) (?:and )?(?:message|body) (.+)$", "send_email", None),
    ]
    fixed = {
        "shutdown": "shutdown", "shut down": "shutdown", "restart": "restart",
        "lock": "lock_pc", "lock pc": "lock_pc", "take screenshot": "screenshot",
        "screenshot": "screenshot", "pause music": "pause_music", "play music": "play_music",
        "increase volume": "volume_up", "volume up": "volume_up",
        "decrease volume": "volume_down", "volume down": "volume_down", "mute": "mute_volume",
    }
    if cleaned in fixed:
        return {"intent": fixed[cleaned], "params": {}}
    for pattern, intent, key in patterns:
        match = re.match(pattern, cleaned_text, re.IGNORECASE)
        if match:
            if intent == "send_whatsapp":
                return {"intent": intent, "params": {"contact": match.group(1).strip(), "message": match.group(2).strip()}}
            if intent == "send_email":
                return {"intent": intent, "params": {"recipient": match.group(1).strip(), "subject": match.group(2).strip(), "body": match.group(3).strip()}}
            return {"intent": intent, "params": {key: match.group(1).strip()}}
    return {"intent": "chat", "params": {"message": text}}


def _normalise(data: IntentResponse, command: str) -> dict:
    """Remove unexpected model arguments and guarantee every router call is safe."""
    allowed = PARAM_KEYS.get(data.intent, set())
    params = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in data.params.items()
        if key in allowed and value is not None
    }
    if data.intent == "chat":
        params["message"] = str(params.get("message") or command)
    required = {"open_app": "app", "close_app": "app", "google_search": "query",
                "youtube_search": "query", "open_website": "url", "create_folder": "path",
                "delete_file": "path", "send_whatsapp": "contact"}
    if data.intent in required and not params.get(required[data.intent]):
        return _fallback(command)
    if data.intent == "send_whatsapp" and not params.get("message"):
        return _fallback(command)
    if data.intent == "send_email" and not all(params.get(key) for key in ("recipient", "subject", "body")):
        return _fallback(command)
    return {"intent": data.intent, "params": params}


_client = genai.Client(api_key=GEMINI_API_KEY) if genai and GEMINI_API_KEY else None
_history: list[tuple[str, str]] = []


def configure_api_key(api_key: str) -> bool:
    """Replace the in-memory Gemini client after a key is updated in Settings."""
    global _client
    key = (api_key or "").strip()
    _client = genai.Client(api_key=key) if genai and key else None
    return _client is not None


def detect_intent(command: str) -> dict:
    """Return a router-compatible command, using Gemini structured output when available."""
    if not _client:
        return _fallback(command)
    try:
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=command,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=IntentResponse,
                temperature=0,
                max_output_tokens=128,
            ),
        )
        parsed = response.parsed
        data = parsed if isinstance(parsed, IntentResponse) else IntentResponse.model_validate(parsed)
        return _normalise(data, command)
    except Exception:
        return _fallback(command)


def ai_chat(message: str) -> str:
    """General Gemini chat with a short in-memory conversational context."""
    if not _client:
        return "I can control your computer commands, but Gemini is not configured."
    context = "\n".join(f"{role}: {content}" for role, content in _history[-8:])
    prompt = ("You are Arya, a concise, friendly Windows desktop assistant. "
              "Answer the user directly.\n" + (f"Conversation:\n{context}\n" if context else "")
              + f"User: {message}")
    try:
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=400),
        )
        answer = response.text.strip()
        _history.extend((("User", message), ("Arya", answer)))
        del _history[:-16]
        return answer
    except Exception:
        return "I can't reach Gemini right now, but I can still handle desktop commands."


def reset_chat():
    _history.clear()
