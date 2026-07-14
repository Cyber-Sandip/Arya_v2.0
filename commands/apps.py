"""Windows application launching helpers."""

import os
from pathlib import Path
import shutil
import subprocess
import webbrowser

from config import APP_PATHS


APP_ALIASES = {
    "google chrome": "chrome",
    "microsoft edge": "edge",
    "mozilla firefox": "firefox",
    "visual studio code": "vscode",
    "vs code": "vscode",
    "code": "vscode",
    "windows explorer": "explorer",
    "file explorer": "explorer",
    "terminal": "powershell",
}


def _normalise_name(name: str) -> str:
    return " ".join(name.casefold().replace("_", " ").replace("-", " ").split())


def _registered_app_path(name: str) -> Path | None:
    """Look up programs registered with Windows' App Paths registry key."""
    try:
        import winreg
    except ImportError:
        return None

    executable_names = [name]
    if not name.lower().endswith(".exe"):
        executable_names.append(f"{name}.exe")
    registry_roots = (
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
    )
    for hive, base_key in registry_roots:
        for executable_name in executable_names:
            try:
                with winreg.OpenKey(hive, f"{base_key}\{executable_name}") as key:
                    value, _ = winreg.QueryValueEx(key, None)
                candidate = Path(os.path.expandvars(value.strip('"')))
                if candidate.is_file():
                    return candidate
            except OSError:
                continue
    return None


def _start_menu_shortcut(name: str) -> Path | None:
    """Find a matching Start Menu shortcut for installed desktop applications."""
    wanted = _normalise_name(name.removesuffix(".exe"))
    roots = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ]
    for root in roots:
        if not root.is_dir():
            continue
        try:
            for shortcut in root.rglob("*.lnk"):
                shortcut_name = _normalise_name(shortcut.stem)
                if shortcut_name == wanted or shortcut_name.startswith(f"{wanted} "):
                    return shortcut
        except OSError:
            continue
    return None


def _resolve_app(name: str) -> Path | str | None:
    configured = APP_PATHS.get(name)
    if configured:
        configured_path = Path(os.path.expandvars(configured))
        if configured_path.is_file() or not configured_path.is_absolute():
            return str(configured_path)

    supplied_path = Path(os.path.expandvars(name)).expanduser()
    if supplied_path.is_file():
        return supplied_path

    on_path = shutil.which(name) or shutil.which(f"{name}.exe")
    if on_path:
        return on_path

    registered = _registered_app_path(name)
    if registered:
        return registered

    return _start_menu_shortcut(name)


def open_app(app=None, value=None):
    name = _normalise_name(app or value or "")
    if not name:
        return {"success": False, "message": "Please specify an application to open."}
    name = APP_ALIASES.get(name, name)
    if name in {"whatsapp", "whatsapp web"}:
        webbrowser.open_new_tab("https://web.whatsapp.com/")
        return {"success": True, "message": "Opening WhatsApp Web."}
    if "." in name and " " not in name:
        address = name if "://" in name else f"https://{name}"
        webbrowser.open_new_tab(address)
        return {"success": True, "message": f"Opening {address}."}

    target = _resolve_app(name)
    if not target:
        return {
            "success": False,
            "message": f"I could not find '{name}'. Use its Start Menu name or add its executable path to APP_PATHS in config.py.",
        }
    try:
        # startfile handles both .exe files and Start Menu .lnk shortcuts.
        os.startfile(str(target))
        return {"success": True, "message": f"Opening {name}."}
    except OSError as error:
        return {"success": False, "message": f"Could not open {name}: {error}"}


def close_app(app=None, value=None):
    name = (app or value or "").strip()
    if not name:
        return {"success": False, "message": "Please specify an application to close."}
    result = subprocess.run(["taskkill", "/IM", f"{name}.exe", "/F"], capture_output=True, text=True)
    if result.returncode == 0:
        return {"success": True, "message": f"Closed {name}."}
    return {"success": False, "message": f"{name} is not running."}


def install_app():
    pass


def uninstall_app():
    pass


def list_app():
    pass
