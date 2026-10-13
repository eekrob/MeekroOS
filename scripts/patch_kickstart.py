#!/usr/bin/env python3
"""Add Meekro RPM requirements to a flattened Fedora Workstation Live Kickstart.

The source kickstart is NOT modified. Never issues disk-changing commands.
"""
import argparse
from pathlib import Path
import re

PACKAGES = (
    "meekro-welcome", "anaconda-live", "anaconda-webui", "python3-gobject",
    "gtk4", "libadwaita", "polkit", "flatpak", "pciutils",
)

POST = """
# Disable original per-liveuser welcome, if source kickstart created one.
# A user autostart .desktop overrides the system-wide /etc/xdg/autostart entry.
if [ -d /home/liveuser ]; then
    mkdir -p /home/liveuser/.config/autostart
    cat > /home/liveuser/.config/autostart/org.fedoraproject.welcome-screen.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Fedora Welcome (disabled by MeekroOS)
Hidden=true
DESKTOP
    chown -R liveuser:liveuser /home/liveuser/.config/autostart || true
fi
# Hide the stock 'Install to Hard Drive' launcher from desktop menus while
# keeping /usr/bin/liveinst and all required Anaconda packages.
mkdir -p /usr/local/share/applications
cat > /usr/local/share/applications/liveinst.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Fedora Live Installer (masked by MeekroOS)
Hidden=true
DESKTOP
"""

def patch(text):
    matches = list(re.finditer(r'(?m)^%packages(?:[ \t]+[^\n]*)?\n', text))
    if len(matches) != 1:
        raise ValueError("Expected one %packages block in flattened kickstart")
    start = matches[0].end()
    end = text.find("\n%end", start)
    if end < 0:
        raise ValueError("Missing %packages %end")
    old = text[start:end]
    missing = [pkg for pkg in PACKAGES if not re.search(r'(?m)^' + re.escape(pkg) + r'\s*$', old)]
    if missing:
        text = text[:end] + "\n# MeekroOS packages\n" + "\n".join(missing) + text[end:]
    if "# MeekroOS Live overlay" not in text:
        text += "\n# MeekroOS Live overlay\n%post\n" + POST + "\n%end\n"
    return text

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path, help="flattened Fedora Workstation Live Kickstart")
    p.add_argument("output", type=Path, help="output patched kickstart")
    args = p.parse_args()
    if args.input.resolve() == args.output.resolve():
        p.error("Input and output must differ")
    args.output.write_text(patch(args.input.read_text(encoding="utf-8")), encoding="utf-8")
    print("Wrote", args.output)

if __name__ == "__main__":
    main()
