from __future__ import annotations

import ipaddress
import re
import shutil

from winshell.adapters.runner import CommandResult, run_command
from winshell.models import NetworkAdapter, NetworkSnapshot


def _available(command: str) -> bool:
    return shutil.which(command) is not None


def _run(command: list[str], timeout: int = 10) -> CommandResult:
    if not command or not _available(command[0]):
        name = command[0] if command else "command"
        return CommandResult(stdout="", stderr=f"{name} is not available on this Mac.", returncode=127)
    return run_command(command, timeout=timeout)


def _hex_netmask_to_ipv4(value: str) -> str:
    try:
        return str(ipaddress.IPv4Address(int(value, 16)))
    except ValueError:
        return value


def _parse_ifconfig(text: str) -> dict[str, NetworkAdapter]:
    adapters: dict[str, NetworkAdapter] = {}
    current: NetworkAdapter | None = None

    for line in text.splitlines():
        if line and not line[0].isspace():
            device = line.split(":", 1)[0]
            current = NetworkAdapter(device=device, name=device)
            adapters[device] = current
            continue

        if current is None:
            continue

        stripped = line.strip()
        if stripped.startswith("ether "):
            current.mac = stripped.split()[1]
        elif stripped.startswith("inet "):
            parts = stripped.split()
            current.ipv4 = parts[1]
            if "netmask" in parts:
                mask_index = parts.index("netmask") + 1
                current.subnet_mask = _hex_netmask_to_ipv4(parts[mask_index])
            if "broadcast" in parts:
                current.broadcast = parts[parts.index("broadcast") + 1]
        elif stripped.startswith("inet6 "):
            ipv6 = stripped.split()[1].split("%", 1)[0]
            if ipv6 not in current.ipv6:
                current.ipv6.append(ipv6)
        elif stripped.startswith("status:"):
            current.status = stripped.split(":", 1)[1].strip()
            current.media = "Media connected" if current.status == "active" else "Media disconnected"
        elif stripped.startswith("mtu "):
            current.mtu = stripped.split()[1]

    return adapters


def _parse_hardware_ports(text: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    current_port = ""

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Hardware Port:"):
            current_port = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Device:") and current_port:
            mapping[stripped.split(":", 1)[1].strip()] = current_port

    return mapping


def _parse_default_route(text: str) -> tuple[str, str]:
    gateway = ""
    interface = ""

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("gateway:"):
            gateway = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("interface:"):
            interface = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("default"):
            parts = stripped.split()
            if len(parts) >= 4 and not parts[1].startswith("link#"):
                gateway = parts[1]
                interface = parts[3]
                break

    return gateway, interface


def _parse_dns(text: str) -> list[str]:
    servers: list[str] = []
    for match in re.findall(r"nameserver\[\d+\]\s*:\s*([^\s]+)", text):
        if match not in servers:
            servers.append(match)
    if servers:
        return servers
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("nameserver "):
            value = stripped.split(None, 1)[1]
            if value not in servers:
                servers.append(value)
    return servers


def _adapter_priority(adapter: NetworkAdapter) -> tuple[int, str]:
    activity_rank = 0 if adapter.status == "active" else 1
    name_rank = 0 if adapter.name != adapter.device else 1
    return activity_rank, f"{name_rank}-{adapter.name}-{adapter.device}"


def network_snapshot() -> NetworkSnapshot:
    host_name = _run(["hostname"]).stdout or "Unavailable"
    ifconfig_result = _run(["ifconfig"], timeout=10)
    networksetup_result = _run(["networksetup", "-listallhardwareports"], timeout=10)
    route_result = _run(["route", "-n", "get", "default"], timeout=5)
    if route_result.returncode != 0 or not route_result.stdout:
        route_result = _run(["netstat", "-rn", "-f", "inet"], timeout=10)
    dns_result = _run(["scutil", "--dns"], timeout=10)
    if not dns_result.stdout:
        dns_result = _run(["sed", "-n", "1,120p", "/etc/resolv.conf"], timeout=5)

    adapters = _parse_ifconfig(ifconfig_result.stdout)
    hardware_ports = _parse_hardware_ports(networksetup_result.stdout)
    default_gateway, default_interface = _parse_default_route(route_result.stdout)

    filtered: list[NetworkAdapter] = []
    for device, adapter in adapters.items():
        adapter.name = hardware_ports.get(device, device)
        adapter.is_default = device == default_interface
        if device.startswith(("lo", "utun", "awdl")):
            continue
        if adapter.ipv4 or adapter.name != device:
            filtered.append(adapter)

    filtered.sort(key=_adapter_priority)
    return NetworkSnapshot(
        host_name=host_name,
        adapters=filtered,
        default_gateway=default_gateway,
        default_interface=default_interface,
        dns_servers=_parse_dns(dns_result.stdout),
    )


def ping_host(host: str, count: int = 4) -> dict[str, object]:
    result = _run(["ping", "-c", str(count), host], timeout=max(8, count * 2))
    if result.returncode not in (0, 2):
        return {"error": result.stderr or result.stdout or "Ping failed."}

    destination = ""
    replies: list[dict[str, str]] = []
    summary: list[str] = []

    for line in result.stdout.splitlines():
        if line.startswith("PING "):
            match = re.search(r"\(([^)]+)\)", line)
            destination = match.group(1) if match else ""
        elif " bytes from " in line and "time=" in line:
            match = re.search(
                r"(?P<bytes>\d+) bytes from (?P<ip>[0-9a-fA-F\.:]+): .*ttl=(?P<ttl>\d+) time=(?P<time>[0-9.]+ ms)",
                line,
            )
            if match:
                replies.append(match.groupdict())
        elif "packets transmitted" in line or "round-trip" in line:
            summary.append(line.strip())

    return {"destination": destination, "replies": replies, "summary": summary}


def traceroute_host(host: str) -> dict[str, object]:
    result = _run(["traceroute", "-m", "16", host], timeout=25)
    if result.returncode != 0:
        return {"error": result.stderr or result.stdout or "Traceroute failed."}

    destination = ""
    hops: list[dict[str, str | list[str]]] = []

    for index, line in enumerate(result.stdout.splitlines()):
        if index == 0:
            match = re.search(r"\(([^)]+)\)", line)
            destination = match.group(1) if match else ""
            continue

        stripped = line.strip()
        if not stripped:
            continue

        hop_match = re.match(r"(\d+)\s+(.*)", stripped)
        if not hop_match:
            continue

        hop_number, rest = hop_match.groups()
        if rest.startswith("*"):
            hops.append({"hop": hop_number, "status": "timeout", "rtts": [], "target": ""})
            continue

        target = ""
        remaining = rest
        host_match = re.match(r"(.+?) \(([^)]+)\)\s+(.*)", rest)
        if host_match:
            target_name, target_ip, remaining = host_match.groups()
            target = f"{target_name} [{target_ip}]"
        else:
            pieces = rest.split()
            target = pieces[0]
            remaining = " ".join(pieces[1:])

        rtts = re.findall(r"([0-9.]+\s+ms)", remaining)
        hops.append({"hop": hop_number, "status": "ok", "rtts": rtts, "target": target})

    return {"destination": destination, "hops": hops}


def netstat_connections(flags: dict[str, str | bool]) -> dict[str, object]:
    if flags and any(flag not in {"-a", "-n", "-an"} for flag in flags):
        return {"unsupported": True}

    result = _run(["netstat", "-an"], timeout=10)
    if result.returncode != 0:
        return {"error": result.stderr or result.stdout or "netstat failed."}

    entries: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped.startswith(("tcp", "udp")):
            continue

        parts = stripped.split()
        if len(parts) < 5:
            continue

        proto = parts[0]
        local = parts[3]
        remote = parts[4]
        state = parts[5] if len(parts) > 5 else ""
        entries.append({"proto": proto, "local": local, "remote": remote, "state": state})

    return {"entries": entries}


def arp_cache() -> dict[str, object]:
    result = _run(["arp", "-a"], timeout=10)
    if result.returncode != 0:
        return {"error": result.stderr or result.stdout or "arp failed."}

    entries: list[dict[str, str]] = []
    pattern = re.compile(
        r".*?\((?P<ip>[^)]+)\) at (?P<mac>\S+) on (?P<interface>\S+)(?: ifscope)?(?: \[(?P<type>[^\]]+)\])?"
    )

    for line in result.stdout.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        entry = match.groupdict()
        entries.append(
            {
                "ip": entry["ip"],
                "mac": entry["mac"].replace(":", "-").upper(),
                "interface": entry["interface"],
                "type": entry["type"] or "dynamic",
            }
        )

    return {"entries": entries}


def nslookup_query(arguments: list[str]) -> dict[str, object]:
    if not arguments:
        return {"error": "Usage: nslookup <host>"}
    result = _run(["nslookup", *arguments], timeout=15)
    if result.returncode != 0:
        return {"error": result.stderr or result.stdout or "nslookup failed."}
    return {"output": result.stdout}


def get_hostname() -> str:
    return _run(["hostname"]).stdout or "Unavailable"


def get_whoami() -> str:
    return _run(["whoami"]).stdout or "Unavailable"
