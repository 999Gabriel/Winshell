from __future__ import annotations

from winshell.adapters.network import get_hostname, get_whoami
from winshell.adapters.runner import run_command
from winshell.models import SystemSnapshot


def _read_sw_vers() -> dict[str, str]:
    data: dict[str, str] = {}
    for line in run_command(["sw_vers"]).stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _read_hardware_overview() -> dict[str, str]:
    data: dict[str, str] = {}
    for line in run_command(["system_profiler", "SPHardwareDataType"], timeout=15).stdout.splitlines():
        stripped = line.strip()
        if ": " not in stripped:
            continue
        key, value = stripped.split(": ", 1)
        data[key.strip()] = value.strip()
    return data


def system_snapshot() -> SystemSnapshot:
    version_info = _read_sw_vers()
    hardware_info = _read_hardware_overview()
    uname = run_command(["uname", "-mrs"]).stdout or "Unavailable"
    architecture = run_command(["uname", "-m"]).stdout

    processor = hardware_info.get("Chip", "") or hardware_info.get("Model Name", "") or "Unavailable"

    return SystemSnapshot(
        host_name=get_hostname(),
        user_name=get_whoami(),
        os_name=version_info.get("ProductName", "macOS"),
        os_version=version_info.get("ProductVersion", "Unavailable"),
        os_build=version_info.get("BuildVersion", "Unavailable"),
        kernel_version=uname,
        architecture=f"{architecture.upper()}-based Mac" if architecture else "Unavailable",
        uptime=uptime_value(),
        processor=processor,
        memory=hardware_info.get("Memory", "Unavailable"),
    )


def process_list(limit: int = 25) -> dict[str, object]:
    result = run_command(["ps", "-axo", "pid=,comm=,%cpu=,%mem=", "-r"], timeout=10)
    if result.returncode != 0:
        return {"error": result.stderr or result.stdout or "Unable to list processes."}
    processes: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        pid, command, cpu, memory = parts
        processes.append({"pid": pid, "image": command.split("/")[-1], "cpu": cpu, "memory": memory})
        if len(processes) >= limit:
            break
    return {"entries": processes}


def uptime_value() -> str:
    result = run_command(["uptime"])
    return result.stdout or result.stderr or "Unavailable"


def who_output() -> str:
    result = run_command(["who"])
    return result.stdout or result.stderr or "No active sessions found."


def last_output(limit: int = 10) -> str:
    result = run_command(["last", f"-{limit}"])
    return result.stdout or result.stderr or "No login history available."
