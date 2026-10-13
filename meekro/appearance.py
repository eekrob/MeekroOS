"""GNOME 50-compatible *best effort* safe appearance configuration."""
import subprocess
from .catalog import BY_ID

EXTENSION_UUID = "blur-my-shell@aunetx"

def apply_theme(theme: str):
    if theme not in {"dark", "light", "system"}:
        raise ValueError("Invalid theme")
    scheme = {"dark": "prefer-dark", "light": "prefer-light", "system": "default"}[theme]
    operations = [
        ["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", scheme],
        ["gsettings", "set", "org.gnome.desktop.interface", "accent-color", "red"],
    ]
    messages=[]
    for cmd in operations:
        try:
            check = subprocess.run(["gsettings", "get", cmd[2], cmd[3]],capture_output=True,text=True,timeout=6)
            if check.returncode:
                messages.append(f"Unavailable GNOME key: {cmd[3]}")
                continue
            ret = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
            messages.append(f"{cmd[3]}: " + ("updated" if ret.returncode == 0 else ret.stderr.strip()))
        except (OSError, subprocess.TimeoutExpired) as exc:
            messages.append(str(exc))
    return messages

def enable_blur():
    try:
        result = subprocess.run(["gnome-extensions", "enable", EXTENSION_UUID],capture_output=True,text=True,timeout=8)
        if result.returncode:
            return "Blur extension not enabled. Install it first and check GNOME compatibility; log out/in if needed. " + result.stderr.strip()
        return "Blur my Shell enabled; effects depend on GNOME and extension settings. Re-login may be required."
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Cannot configure Blur my Shell: {exc}"
