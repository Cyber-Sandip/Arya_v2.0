"""
=========================================================
Project : Arya V2.0
Author  : Sandip Hazra
Description : AI Desktop Assistant Configuration
=========================================================
"""

from pathlib import Path
from dotenv import load_dotenv
import os


# -------------------------------------------------------
# Load Environment Variables
# -------------------------------------------------------

load_dotenv()

# -------------------------------------------------------
# Project Information
# -------------------------------------------------------

PROJECT_NAME = "Arya V2.0"
ASSISTANT_NAME = "Arya"
VERSION = "2.0.0"
AUTHOR = "Sandip Hazra"

DEBUG = True

# -------------------------------------------------------
# Directories
# -------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"
TEMP_DIR = BASE_DIR / "temp"
PLUGIN_DIR = BASE_DIR / "plugins"
MODEL_DIR = BASE_DIR / "models"
DOWNLOAD_DIR = BASE_DIR / "downloads"

for folder in [
    DATA_DIR,
    LOG_DIR,
    CACHE_DIR,
    TEMP_DIR,
    PLUGIN_DIR,
    MODEL_DIR,
    DOWNLOAD_DIR,
]:
    folder.mkdir(exist_ok=True)

# -------------------------------------------------------
# Gemini
# -------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Override this in .env if you have access to a different Gemini model.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Email (configure these in .env; use an app password for Gmail).
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# -------------------------------------------------------
# User
# -------------------------------------------------------

USER_NAME = os.getenv("USERNAME", "User")

# -------------------------------------------------------
# Voice Settings
# -------------------------------------------------------

VOICE_ENABLED = True

WAKE_WORD = "arya"

LANGUAGE = "en-IN"

VOICE_RATE = 180

VOICE_VOLUME = 1.0

VOICE_GENDER = "female"

# -------------------------------------------------------
# Memory
# -------------------------------------------------------

MEMORY_ENABLED = True

MAX_CHAT_HISTORY = 50

# -------------------------------------------------------
# Files
# -------------------------------------------------------

CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"

MEMORY_FILE = DATA_DIR / "memory.json"

SETTINGS_FILE = DATA_DIR / "settings.json"

COMMAND_HISTORY_FILE = DATA_DIR / "command_history.json"

# -------------------------------------------------------
# MongoDB
# -------------------------------------------------------

MONGO_URI = os.getenv("MONGO_URI")

DATABASE_NAME = "arya"

# -------------------------------------------------------
# Logging
# -------------------------------------------------------

LOG_LEVEL = "INFO"

LOG_FILE = LOG_DIR / "arya.log"

ERROR_LOG = LOG_DIR / "error.log"

# -------------------------------------------------------
# Screenshot
# -------------------------------------------------------

SCREENSHOT_DIR = DATA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------
# Browser
# -------------------------------------------------------

DEFAULT_BROWSER = "chrome"

# -------------------------------------------------------
# AI Settings
# -------------------------------------------------------

AI_FALLBACK = True

MAX_RESPONSE_LENGTH = 4000

REQUEST_TIMEOUT = 30

# -------------------------------------------------------
# Themes
# -------------------------------------------------------

THEME = "dark"

PRIMARY_COLOR = "#00E5FF"

SECONDARY_COLOR = "#0088FF"

# -------------------------------------------------------
# Security
# -------------------------------------------------------

ENABLE_FACE_LOGIN = True

ENABLE_PASSWORD_LOGIN = True

ADMIN_MODE = False

# -------------------------------------------------------
# OCR
# -------------------------------------------------------

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -------------------------------------------------------
# Plugins
# -------------------------------------------------------

PLUGINS_ENABLED = True

AUTO_LOAD_PLUGINS = True

# -------------------------------------------------------
# Applications
# -------------------------------------------------------

APP_PATHS = {

    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",

    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",

    "vscode": fr"C:\Users\{USER_NAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe",

    "spotify": fr"C:\Users\{USER_NAME}\AppData\Roaming\Spotify\Spotify.exe",

    "notepad": "notepad.exe",

    "calculator": "calc.exe",

    "paint": "mspaint.exe",

    "cmd": "cmd.exe",

    "powershell": "powershell.exe",

    "task manager": "taskmgr.exe",

    "explorer": "explorer.exe",

}
