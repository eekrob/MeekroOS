"""Read-only hardware inventory; explicitly no unreviewed driver changes."""
import os
import platform
import shutil
import subprocess

def _try_command(argv, timeout=7):
    if not shutil.which(argv[0]):
        return "Unavailable (install pciutils)"
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return (proc.stdout.strip() or proc.stderr.strip() or "No data")[:8000]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Hardware query failed: {exc}"

def _memory_gib():
    try:
        for line in open("/proc/meminfo", encoding="ascii"):
            if line.startswith("MemTotal:"):
                return f"{int(line.split()[1]) / 1024 / 1024:.1f} GiB"
    except (OSError, ValueError):
        pass
    return "unknown"

def _cpu_model():
    try:
        for line in open("/proc/cpuinfo", encoding="ascii"):
            if line.startswith("model name"):
                return line.partition(":")[2].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"

def collect():
    return {
        "cpu": _cpu_model(),
        "logical_cores": str(os.cpu_count() or "unknown"),
        "ram": _memory_gib(),
        "system": platform.platform(),
        "architecture": platform.machine(),
        "session": os.environ.get("XDG_SESSION_TYPE", "unknown"),
        "video_devices": "\n".join(line for line in _try_command(["lspci", "-nn"]).splitlines() if "VGA" in line or "3D controller" in line or "Display controller" in line) or "No GPU detected",
    }

def driver_advice(info):
    info_str = info.get("video_devices", "").lower()
    if "nvidia" in info_str:
        return "NVIDIA detected. Proprietary driver requires explicit approval and may require RPM Fusion, Secure Boot signing and a reboot. No driver changes are automatic."
    if "amd" in info_str or "advanced micro devices" in info_str:
        return "AMD graphics detected. Fedora Mesa/amdgpu stack is usually appropriate."
    if "intel" in info_str:
        return "Intel graphics detected. Fedora Mesa/i915/xe driver stack is usually appropriate."
    return "GPU driver recommendations are informational only."
