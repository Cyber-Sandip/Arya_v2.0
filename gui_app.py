"""PyWebView bridge for the Arya Command Deck UI."""

import json
import os
import re
import threading
import time
from pathlib import Path

import psutil
import webview

from ai.gemini import configure_api_key, detect_intent
from config import SETTINGS_FILE
from router import execute
from voice.speech_to_text import listen, set_voice_callbacks
from voice.text_to_speech import speak


DEFAULT_SETTINGS = {
    "maintenance_mode": False,
    "voice_auto_start": False,
    "camera_enabled": True,
    "mic_visualizer": False,
}


class AryaGuiApi:
    def __init__(self):
        self._settings = self._load_settings()
        self._history = []
        self._voice_running = False
        self._voice_thread = None
        self._lock = threading.Lock()
        self._voice = {"phase": "idle", "message": "Ready for command", "mic_level": 0}
        set_voice_callbacks(self._voice_status, self._voice_level)

    def _load_settings(self):
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8")) if SETTINGS_FILE.exists() else {}
            return {**DEFAULT_SETTINGS, **saved}
        except (OSError, json.JSONDecodeError):
            return DEFAULT_SETTINGS.copy()

    def _save_settings(self):
        SETTINGS_FILE.write_text(json.dumps(self._settings, indent=2), encoding="utf-8")

    def _voice_status(self, phase, message=None, mic_level=None):
        with self._lock:
            self._voice.update({"phase": phase, "message": message or phase.title()})
            if mic_level is not None:
                self._voice["mic_level"] = mic_level

    def _voice_level(self, level):
        with self._lock:
            self._voice["mic_level"] = level

    def _record(self, command, source="gui", result=None):
        with self._lock:
            self._history.append({"command": command, "source": source, "ts": time.time(), "result": result or ""})
            del self._history[:-50]

    def _run_command(self, command, source):
        command = (command or "").strip()
        if not command:
            return {"success": False, "message": "Enter a command first."}
        self._voice_status("thinking", "Understanding command", 0)
        data = detect_intent(command)
        intent, params = data.get("intent", "chat"), data.get("params") or {}
        result = execute(intent, params)
        message = result.get("message", "Done.") if isinstance(result, dict) else str(result)
        self._record(command, source, message)
        self._voice_status("heard", message, 0)
        speak(message)
        return {"success": bool(result.get("success", True)), "message": message, "intent": intent}

    def _voice_worker(self):
        self._voice_status("listening", "Listening...", 8)
        while self._voice_running:
            command = listen()
            if command:
                self._run_command(command, "voice")
            elif self._voice_running:
                self._voice_status("listening", "Listening...", 8)
        self._voice_status("idle", "Voice stopped", 0)

    # Methods below are called by Gui/main.js through window.pywebview.api.
    def get_settings(self):
        return self._settings.copy()

    def update_settings(self, settings):
        allowed = set(DEFAULT_SETTINGS)
        self._settings.update({key: bool(value) for key, value in (settings or {}).items() if key in allowed})
        self._save_settings()
        return {"success": True, "settings": self._settings.copy()}

    def get_gemini_status(self):
        return {"configured": bool(os.getenv("GEMINI_API_KEY")), "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")}

    def update_gemini_key(self, api_key):
        """Persist a Gemini key privately and activate it without restarting Arya."""
        key = (api_key or "").strip()
        if not key:
            return {"success": False, "message": "Enter a Gemini API key first."}
        env_path = Path(__file__).resolve().parent / ".env"
        try:
            current = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
            line = f"GEMINI_API_KEY={key}"
            if re.search(r"(?m)^\s*GEMINI_API_KEY\s*=.*$", current):
                current = re.sub(r"(?m)^\s*GEMINI_API_KEY\s*=.*$", line, current)
            else:
                current = current.rstrip("\r\n") + ("\n" if current.strip() else "") + line + "\n"
            env_path.write_text(current, encoding="utf-8")
            os.environ["GEMINI_API_KEY"] = key
            configure_api_key(key)
            return {"success": True, "message": "Gemini API key saved and activated."}
        except OSError as error:
            return {"success": False, "message": f"Could not save the Gemini key: {error}"}

    def submit_command(self, command):
        return self._run_command(command, "typed")

    def start_arya(self):
        if self._voice_running:
            return {"success": True, "message": "Voice listener is already running."}
        self._voice_running = True
        self._voice_thread = threading.Thread(target=self._voice_worker, name="arya-voice", daemon=True)
        self._voice_thread.start()
        return {"success": True, "message": "Voice listener started."}

    def arya_status(self):
        with self._lock:
            return {"running": self._voice_running, "voice": self._voice.copy()}

    def microphone_status(self):
        try:
            import speech_recognition as sr
            names = sr.Microphone.list_microphone_names()
            return {"status": "ok" if names else "error", "message": "Microphone ready." if names else "No microphone was found."}
        except Exception as error:
            return {"status": "error", "message": f"Microphone unavailable: {error}"}

    def system_status(self):
        battery = psutil.sensors_battery()
        return {
            "cpu": psutil.cpu_percent(interval=None),
            "memory": psutil.virtual_memory().percent,
            "battery": battery.percent if battery else None,
            "plugged": bool(battery.power_plugged) if battery else False,
            "voice_running": self._voice_running,
            "voice": self.arya_status()["voice"],
            "maintenance_mode": self._settings["maintenance_mode"],
        }

    def get_history(self):
        with self._lock:
            return {"history": self._history.copy()}

    def clear_history(self):
        with self._lock:
            self._history.clear()
        return {"success": True}

    def quick_action(self, action):
        commands = {
            "google": "open google.com", "youtube": "open youtube.com", "gmail": "open gmail.com",
            "explorer": "open explorer", "calendar": "open calendar.google.com", "logs": "open logs folder",
        }
        if action == "logs":
            import os
            os.startfile(str(Path(__file__).resolve().parent / "logs"))
            return {"success": True, "message": "Opening logs folder."}
        if action not in commands:
            return {"success": False, "message": "This shortcut is not available."}
        return self._run_command(commands[action], "shortcut")


def run_gui():
    root = Path(__file__).resolve().parent
    api = AryaGuiApi()
    window = webview.create_window("Arya V2.0 — Command Deck", (root / "Gui" / "index.html").as_uri(), js_api=api, width=1440, height=920, min_size=(920, 650))
    webview.start(debug=False)
    api._voice_running = False


if __name__ == "__main__":
    run_gui()
