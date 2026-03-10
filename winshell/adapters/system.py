from __future__ import annotations

from winshell.adapters.network import get_hostname, get_whoami
from winshell.adapters.runner import run_command
from winshell.models import SystemSnapshot


def _read_hardware_overview() -> dict[str, str]:
    data: dict[str, str] = {}
    for line in run_command(["system_profiler", "SPHardwareDataType"], timeout=15).stdout.splitlines():
        stripped = line.strip()
        if ": " not in stripped:
            continue
        key, value = stripped.split(": ", 1)
        data[key.strip()] = value.strip()
    return data


def _read_sw_vers() -> dict[str, str]:
    data: dict[str, str] = {}
    for line in run_command(["sw_vers"]).stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def system_snapshot() -> SystemSnapshot:
    version_info = _read_sw_vers()
    hardware_info = _read_hardware_overview()
    uname = run_command(["uname", "-mrs"]).stdout or "Unavailable"
    architecture = run_command(["uname", "-m"]).stdout
    uptime = run_command(["uptime"]).stdout or "Unavailable"

    memory = hardware_info.get("Memory", "Unavailable")

    processor = hardware_info.get("Chip", "")
    if not processor:
        processor = hardware_info.get("Model Name", "")
    if not processor:
        processor = "Unavailable"

    return SystemSnapshot(
        host_name=get_hostname(),
        user_name=get_whoami(),
        os_name=version_info.get("ProductName", "macOS"),
        os_version=version_info.get("ProductVersion", "Unavailable"),
        os_build=version_info.get("BuildVersion", "Unavailable"),
        kernel_version=uname,
        architecture=f"{architecture.upper()}-based Mac" if architecture else "Unavailable",
        uptime=uptime,
        processor=processor,
        memory=memory,
    )
