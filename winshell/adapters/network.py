from __future__ import annotations

import ipaddress
import json
from pathlib import Path
import re
import shutil
import socket
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from winshell.adapters.runner import CommandResult, run_command
from winshell.models import NetworkAdapter, NetworkSnapshot

try:
    import certifi
except ImportError:  # pragma: no cover - dependency should be present at runtime
    certifi = None


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
                current.subnet_mask = _hex_netmask_to_ipv4(parts[parts.index("netmask") + 1])
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
        dns_result = CommandResult(stdout=_read_resolv_conf(), stderr="", returncode=0)

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


def _read_resolv_conf() -> str:
    path = Path("/etc/resolv.conf")
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


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


def route_table() -> dict[str, object]:
    result = _run(["netstat", "-rn", "-f", "inet"], timeout=10)
    if result.returncode != 0:
        return {"error": result.stderr or result.stdout or "Route table lookup failed."}

    entries: list[dict[str, str]] = []
    in_inet_block = False
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped == "Internet:":
            in_inet_block = True
            continue
        if not in_inet_block or not stripped or stripped.startswith("Destination"):
            continue
        if stripped.endswith(":"):
            break

        parts = stripped.split()
        if len(parts) < 4:
            continue
        destination = parts[0]
        gateway = parts[1]
        flags = parts[2]
        interface = parts[3]
        entries.append(
            {
                "destination": destination,
                "gateway": gateway,
                "flags": flags,
                "interface": interface,
            }
        )

    return {"entries": entries}


def mac_addresses() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for adapter in network_snapshot().adapters:
        if not adapter.mac:
            continue
        entries.append(
            {
                "physical_address": adapter.mac.replace(":", "-").upper(),
                "transport": adapter.device,
                "adapter": adapter.name,
            }
        )
    return entries


def resolve_host(host: str) -> dict[str, object]:
    ipv4: list[str] = []
    ipv6: list[str] = []
    reverse: list[str] = []
    errors: list[str] = []

    try:
        for family, _, _, canonical_name, sockaddr in socket.getaddrinfo(host, None):
            address = sockaddr[0]
            if family == socket.AF_INET and address not in ipv4:
                ipv4.append(address)
            elif family == socket.AF_INET6 and address not in ipv6:
                ipv6.append(address)
    except socket.gaierror as exc:
        errors.append(str(exc))

    for address in (ipv4 + ipv6)[:3]:
        try:
            reverse_name = socket.gethostbyaddr(address)[0]
            if reverse_name not in reverse:
                reverse.append(reverse_name)
        except (socket.herror, socket.gaierror):
            continue

    dig_lines: list[str] = []
    dig_result = _run(["dig", "+short", host], timeout=15)
    if dig_result.returncode == 0 and dig_result.stdout:
        dig_lines = [line for line in dig_result.stdout.splitlines() if line.strip()]

    nslookup_result = nslookup_query([host])
    if "error" in nslookup_result and not ipv4 and not ipv6:
        errors.append(str(nslookup_result["error"]))

    return {
        "canonical_name": socket.getfqdn(host),
        "ipv4": ipv4,
        "ipv6": ipv6,
        "reverse": reverse,
        "dig": dig_lines,
        "nslookup": str(nslookup_result.get("output", "")).strip(),
        "errors": errors,
    }


def dig_query(arguments: list[str]) -> dict[str, object]:
    result = _run(["dig", *arguments], timeout=15)
    if result.returncode != 0:
        return {"error": result.stderr or result.stdout or "dig failed."}
    return {"output": result.stdout}


def tcp_probe(host: str, port: int, timeout: float = 3.0) -> dict[str, object]:
    result: dict[str, object] = {
        "host": host,
        "port": port,
        "resolved": "",
        "success": False,
        "latency_ms": "",
        "error": "",
    }

    try:
        resolved = socket.gethostbyname(host)
        result["resolved"] = resolved
    except socket.gaierror as exc:
        result["error"] = str(exc)
        return result

    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency_ms = (time.perf_counter() - started) * 1000
            result["success"] = True
            result["latency_ms"] = f"{latency_ms:.1f}"
    except OSError as exc:
        result["error"] = str(exc)

    return result


def get_hostname() -> str:
    return _run(["hostname"]).stdout or "Unavailable"


def get_whoami() -> str:
    return _run(["whoami"]).stdout or "Unavailable"


def _safe_reverse_lookup(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror, OSError):
        return ""


def _resolve_target(target: str) -> dict[str, str]:
    reverse_name = ""
    try:
        ipaddress.ip_address(target)
        resolved = target
        reverse_name = _safe_reverse_lookup(target)
        canonical_name = reverse_name or target
    except ValueError:
        try:
            resolved = socket.gethostbyname(target)
        except socket.gaierror as exc:
            return {"error": str(exc)}
        canonical_name = socket.getfqdn(target)
        reverse_name = _safe_reverse_lookup(resolved)
    except socket.gaierror as exc:
        return {"error": str(exc)}
    return {
        "target": target,
        "resolved": resolved,
        "canonical_name": canonical_name,
        "reverse_name": reverse_name,
    }


def _ip_scope(ip: str) -> str:
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return "unknown"
    if address.is_loopback:
        return "loopback"
    if address.is_private:
        return "private"
    if address.is_multicast:
        return "multicast"
    if address.is_reserved:
        return "reserved"
    return "public"


def _tls_context() -> ssl.SSLContext:
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def geoip_lookup(target: str) -> dict[str, object]:
    resolution = _resolve_target(target)
    if "error" in resolution:
        return {"error": resolution["error"]}

    resolved = resolution["resolved"]
    scope = _ip_scope(resolved)
    result: dict[str, object] = {
        **resolution,
        "scope": scope,
        "coordinates": "",
        "map_links": {},
    }

    if scope != "public":
        result["note"] = "Private, loopback, or reserved addresses cannot be geolocated on a public map."
        return result

    request = Request(
        f"https://ipwho.is/{resolved}",
        headers={"User-Agent": "WinShell/0.1"},
    )
    try:
        with urlopen(request, timeout=6, context=_tls_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {"error": f"Geolocation lookup failed: {exc}"}

    if not payload.get("success", True):
        message = payload.get("message", "Unknown geolocation lookup failure.")
        return {"error": f"Geolocation lookup failed: {message}"}

    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    coordinates = ""
    map_links: dict[str, str] = {}
    if latitude is not None and longitude is not None:
        coordinates = f"{latitude}, {longitude}"
        map_links = {
            "Apple Maps": f"https://maps.apple.com/?ll={latitude},{longitude}&q={resolved}",
            "Google Maps": f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}",
            "OpenStreetMap": f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=10/{latitude}/{longitude}",
        }

    connection = payload.get("connection") or {}
    timezone = payload.get("timezone") or {}
    result.update(
        {
            "country": payload.get("country", ""),
            "region": payload.get("region", ""),
            "city": payload.get("city", ""),
            "coordinates": coordinates,
            "timezone": timezone.get("id", "") or timezone.get("abbr", ""),
            "isp": connection.get("isp", ""),
            "org": connection.get("org", ""),
            "asn": str(connection.get("asn", "")),
            "map_links": map_links,
        }
    )
    return result


def neighbor_devices() -> dict[str, object]:
    arp_result = arp_cache()
    if "error" in arp_result:
        return {"error": arp_result["error"]}

    seen: set[tuple[str, str]] = set()
    neighbors: list[dict[str, str]] = []
    for entry in arp_result.get("entries", []):
        ip = entry["ip"]
        try:
            address = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if address.is_multicast or address.is_loopback or address.is_unspecified:
            continue
        if entry["mac"].upper() == "FF-FF-FF-FF-FF-FF":
            continue
        key = (ip, entry["interface"])
        if key in seen:
            continue
        seen.add(key)
        neighbors.append(
            {
                "ip": ip,
                "hostname": _safe_reverse_lookup(ip) or "Unavailable",
                "mac": entry["mac"],
                "interface": entry["interface"],
                "scope": _ip_scope(ip),
                "type": entry["type"],
            }
        )

    neighbors.sort(key=lambda item: (item["scope"] != "private", item["interface"], item["ip"]))
    return {"entries": neighbors}


def inspect_target(target: str) -> dict[str, object]:
    resolution = _resolve_target(target)
    if "error" in resolution:
        return {"error": resolution["error"]}

    resolved = resolution["resolved"]
    snapshot = network_snapshot()
    local_adapter = next((adapter for adapter in snapshot.adapters if adapter.ipv4 == resolved), None)

    arp_result = arp_cache()
    arp_entry = None
    if "entries" in arp_result:
        arp_entry = next((entry for entry in arp_result["entries"] if entry["ip"] == resolved), None)

    result: dict[str, object] = {
        **resolution,
        "scope": _ip_scope(resolved),
        "is_local": local_adapter is not None or target in {"localhost", snapshot.host_name},
        "mac": arp_entry["mac"] if arp_entry else (local_adapter.mac.replace(":", "-").upper() if local_adapter and local_adapter.mac else ""),
        "interface": arp_entry["interface"] if arp_entry else (local_adapter.device if local_adapter else ""),
        "adapter_name": local_adapter.name if local_adapter else "",
        "architecture_note": "Remote architecture cannot be inferred reliably without active fingerprinting or agent access.",
    }

    if result["scope"] == "public":
        geo = geoip_lookup(resolved)
        if "error" not in geo:
            result["geo"] = geo
        else:
            result["geo_error"] = geo["error"]
    return result
