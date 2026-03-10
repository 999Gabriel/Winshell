from __future__ import annotations

import platform
from datetime import datetime

from winshell.adapters.runner import run_command


def get_systeminfo() -> dict:
    sw_vers = run_command(["sw_vers"]).stdout
    uname = run_command(["uname", "-a"]).stdout.strip()
    cpu = run_command(["sysctl", "-n", "machdep.cpu.brand_string"]).stdout.strip()
    mem_bytes = run_command(["sysctl", "-n", "hw.memsize"]).stdout.strip()
    serial = run_command([
        "system_profiler",
        "SPHardwareDataType",
    ]).stdout

    mem_gb = "Unknown"
    if mem_bytes.isdigit():
        mem_gb = f"{round(int(mem_bytes) / (1024**3), 1)} GB"

    return {
        "host": platform.node(),
        "os": sw_vers,
        "kernel": uname,
        "cpu": cpu,
        "memory": mem_gb,
        "arch": platform.machine(),
        "python": platform.python_version(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hardware_blob": serial,
    }
