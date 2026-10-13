"""Package installation pipeline. Only allowlisted package IDs become process arguments."""
import shutil
import subprocess
from dataclasses import dataclass
from collections.abc import Callable
from .catalog import BY_ID

FLATHUB_URL = "https://flathub.org/repo/flathub.flatpakrepo"
class InstallError(RuntimeError):
    pass

@dataclass(frozen=True)
class Step:
    title: str
    argv: tuple[str, ...]


def build_plan(selected, allow_flathub: bool) -> list[Step]:
    if any(x not in BY_ID for x in selected):
        raise InstallError("Catalog ID not allowed")
    chosen = [BY_ID[x] for x in dict.fromkeys(selected)]
    rpm = [x.package for x in chosen if x.kind == "dnf"]
    flatpak = [x for x in chosen if x.kind == "flatpak"]
    if flatpak and not allow_flathub:
        raise InstallError("Flathub consent required for Flatpak choices")
    out = []
    if rpm:
        # System RPM packages are installed only after polkit confirmation.
        out.append(Step("Install Fedora RPM packages", ("pkexec", "/usr/bin/dnf5", "install", "--assumeyes", *rpm)))
    if flatpak:
        out.append(Step("Enable Flathub (user remote)", ("flatpak", "remote-add", "--user", "--if-not-exists", "flathub", FLATHUB_URL)))
        for item in flatpak:
            out.append(Step(f"Install {item.title}", ("flatpak", "install", "--user", "--assumeyes", "flathub", item.package)))
    return out

def missing_programs(plan):
    return sorted({step.argv[0] for step in plan if not shutil.which(step.argv[0])})

def run_plan(plan: list[Step], report: Callable[[str], None], cancelled: Callable[[], bool]):
    """Cancellation is safe BETWEEN transactions; don't interrupt RPM mid-transaction."""
    results = []
    for idx, step in enumerate(plan, 1):
        if cancelled():
            report("Stopped before next transaction. Existing changes were not rolled back.")
            return results
        report(f"[{idx}/{len(plan)}] {step.title}")
        try:
            p = subprocess.Popen(step.argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
            assert p.stdout is not None
            for line in p.stdout:
                report(line.rstrip("\r\n")[:1500])
            code = p.wait()
        except OSError as exc:
            code = -1
            report(f"Could not start: {exc}")
        results.append((step.title, code))
        if code:
            report(f"Operation failed (exit {code}); stopping. You may retry.")
            break
    return results


def installed(item_id: str) -> bool:
    item = BY_ID[item_id]
    try:
        if item.kind == "dnf":
            argv = ["rpm", "-q", item.package]
        else:
            argv = ["flatpak", "info", "--user", item.package]
        return subprocess.run(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False
