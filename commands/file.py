import os
import shutil
from pathlib import Path

def _path(value):
    return Path(value).expanduser().resolve()

def create_file(path=None, name=None, content=""):
    value = path or name
    if not value:
        return {"success": False, "message": "Please provide a file path."}
    target = _path(value)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"success": True, "message": f"Created file {target.name}."}

def create_folder(path=None, name=None):
    value = path or name
    if not value:
        return {"success": False, "message": "Please provide a folder path."}
    target = _path(value)
    target.mkdir(parents=True, exist_ok=True)
    return {"success": True, "message": f"Created folder {target.name}."}

def delete_file(path=None, name=None):
    value = path or name
    if not value:
        return {"success": False, "message": "Please provide a file path."}
    target = _path(value)
    if not target.is_file():
        return {"success": False, "message": "File not found."}
    target.unlink()
    return {"success": True, "message": f"Deleted file {target.name}."}

def delete_folder(path=None, name=None):
    value = path or name
    if not value:
        return {"success": False, "message": "Please provide a folder path."}
    target = _path(value)
    if not target.is_dir():
        return {"success": False, "message": "Folder not found."}
    shutil.rmtree(target)
    return {"success": True, "message": f"Deleted folder {target.name}."}

def copy_file(source=None, destination=None):
    shutil.copy2(_path(source), _path(destination))
    return {"success": True, "message": "File copied."}

def rename_file(path=None, new_name=None):
    target = _path(path)
    renamed = target.with_name(new_name)
    target.rename(renamed)
    return {"success": True, "message": f"Renamed to {renamed.name}."}

def compress():
    pass

def extract_file():
    pass

def search_file(query=None, directory=None):
    root = _path(directory or Path.cwd())
    matches = [str(item) for item in root.rglob(f"*{query or ''}*")][:10]
    return {"success": True, "message": "\n".join(matches) if matches else "No matching files found."}


