"""Strictly validated portable settings without executable content."""
from pathlib import Path
import json
import os
from .catalog import BY_ID

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home()/".config")) / "meekro"
STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home()/".local"/"state")) / "meekro"
CONFIG_FILE = CONFIG_DIR / "preferences.json"
COMPLETE_FILE = STATE_DIR / "first-run-complete"

class SettingsError(ValueError):
    pass

def normalize(raw):
    if not isinstance(raw, dict):
        raise SettingsError("Settings must be a JSON object")
    if raw.get("version", 1) != 1:
        raise SettingsError("Unsupported settings version")
    ids = raw.get("selected", [])
    if not isinstance(ids, list) or any(not isinstance(x, str) or x not in BY_ID for x in ids):
        raise SettingsError("Invalid software selection")
    theme = raw.get("theme", "dark")
    if theme not in {"dark", "light", "system"}:
        raise SettingsError("Unknown theme")
    blur = raw.get("blur", False)
    flathub = raw.get("flathub", False)
    if not isinstance(blur, bool) or not isinstance(flathub, bool):
        raise SettingsError("Invalid boolean")
    return {"version": 1, "selected": sorted(set(ids)), "theme": theme, "blur": blur, "flathub": flathub}

def defaults():
    return normalize({"selected": [], "theme": "dark", "blur": False, "flathub": False})

def read(path=CONFIG_FILE):
    p = Path(path)
    if not p.exists():
        return defaults()
    return normalize(json.loads(p.read_text(encoding="utf-8")))

def write(data, path=CONFIG_FILE):
    target = Path(path)
    clean = normalize(data)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = target.with_suffix(target.suffix+".tmp")
    tmp.write_text(json.dumps(clean, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, target)
    return clean

def is_complete():
    return COMPLETE_FILE.exists()

def mark_complete():
    COMPLETE_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    COMPLETE_FILE.write_text("1\n", encoding="utf-8")
