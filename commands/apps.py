import os
import subprocess
import webbrowser
from config import APP_PATHS


def open_app(app=None, value=None):
    name = (app or value or "").strip().lower()
    if not name:
        return {"success": False, "message": "Please specify an application to open."}
    if name in {"whatsapp", "whatsapp web"}:
        webbrowser.open_new_tab("https://web.whatsapp.com/")
        return {"success": True, "message": "Opening WhatsApp Web."}
    if "." in name and " " not in name:
        address = name if "://" in name else f"https://{name}"
        webbrowser.open_new_tab(address)
        return {"success": True, "message": f"Opening {address}."}
    target = APP_PATHS.get(name, name)
    try:
        if os.path.isabs(target) and not os.path.exists(target):
            return {"success": False, "message": f"{name.title()} is not installed at its configured path."}
        subprocess.Popen([target], shell=False)
        return {"success": True, "message": f"Opening {name}."}
    except (OSError, ValueError) as error:
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
