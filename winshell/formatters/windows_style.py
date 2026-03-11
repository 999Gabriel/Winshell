from __future__ import annotations

from pathlib import Path

from winshell.commands.base import CommandSpec
from winshell.models import NetworkSnapshot, SystemSnapshot


def _rows(items: list[tuple[str, str]], indent: int = 3) -> list[str]:
    width = max((len(label) for label, _ in items), default=0)
    prefix = " " * indent
    return [f"{prefix}{label.ljust(width)} : {value}" for label, value in items]


def format_banner(mode: str, cwd: Path) -> str:
    prompt = "PS>" if mode == "powershell" else "C:\\>"
    mode_label = "PowerShell" if mode == "powershell" else "CMD"
    return "\n".join(
        [
            "WinShell for macOS",
            "Windows-style networking and system commands for school labs",
            f"Mode: {mode_label}    Working Directory: {cwd}",
            "Type HELP for a command list, MODE CMD for a classic prompt, or EXIT to quit.",
            f"Prompt preview: {prompt}",
        ]
    )


def format_help(command_rows: list[dict[str, str]]) -> str:
    lines = [
        "WinShell Help",
        "",
        "Supported commands:",
    ]
    for row in command_rows:
        suffix = ""
        if row["permission_level"] != "normal":
            suffix = f" [{row['permission_level']}]"
        alias_text = f" (aliases: {row['aliases']})" if row["aliases"] else ""
        lines.append(f"  {row['name'].ljust(20)} {row['summary']}{alias_text}{suffix}")
    lines.extend(
        [
            "",
            "Examples:",
            "  ipconfig /all",
            "  route print",
            "  getmac",
            "  neighbors",
            "  geoip 8.8.8.8",
            "  deviceinfo localhost",
            "  tasklist",
            "  resolve openai.com",
            "  test-netconnection example.com -port 443",
        ]
    )
    return "\n".join(lines)


def format_command_help(spec: CommandSpec) -> str:
    lines = [
        f"Command: {spec.name}",
        "",
        f"Usage: {spec.usage}",
        f"Summary: {spec.summary}",
        f"Permission Level: {spec.permission_level}",
    ]
    if spec.aliases:
        lines.append(f"Aliases: {', '.join(spec.aliases)}")
    if spec.examples:
        lines.append("")
        lines.append("Examples:")
        lines.extend(f"  {example}" for example in spec.examples)
    return "\n".join(lines)


def format_unknown(cmd: str) -> str:
    return f"'{cmd}' is not recognized as an internal or supported WinShell command."


def format_unsupported() -> str:
    return "Command not supported yet in WinShell."


def format_ipconfig(snapshot: NetworkSnapshot, detailed: bool = False) -> str:
    lines = ["Windows IP Configuration", ""]
    lines.extend(
        _rows(
            [
                ("Host Name", snapshot.host_name),
                ("Default Gateway", snapshot.default_gateway or "Unavailable"),
                ("DNS Servers", ", ".join(snapshot.dns_servers) or "Unavailable"),
            ]
        )
    )
    lines.append("")

    adapters = snapshot.adapters if detailed else [adapter for adapter in snapshot.adapters if adapter.ipv4]
    if not adapters:
        lines.append("No active adapters were detected.")
        return "\n".join(lines)

    for adapter in adapters:
        adapter_title = adapter.name or adapter.device
        if adapter.is_default:
            adapter_title = f"{adapter_title} (Default Route)"
        title_lower = adapter_title.lower()
        if "wi-fi" in title_lower or "wifi" in title_lower:
            prefix = "Wireless LAN"
        elif "ethernet" in title_lower:
            prefix = "Ethernet"
        else:
            prefix = "Network"
        lines.append(f"{prefix} adapter {adapter_title}:")

        details = [
            ("Description", f"{adapter.name} [{adapter.device}]"),
            ("Physical Address", adapter.mac.replace(":", "-").upper() or "Unavailable"),
            ("IPv4 Address", adapter.ipv4 or "Unavailable"),
            ("Subnet Mask", adapter.subnet_mask or "Unavailable"),
            ("Default Gateway", snapshot.default_gateway if adapter.is_default else ""),
        ]
        if detailed:
            details.extend(
                [
                    ("IPv6 Address", ", ".join(adapter.ipv6) or "Unavailable"),
                    ("Media State", adapter.media or adapter.status.title()),
                    ("MTU", adapter.mtu or "Unavailable"),
                ]
            )
            if snapshot.dns_servers:
                details.append(("DNS Servers", ", ".join(snapshot.dns_servers)))

        lines.extend(_rows(details))
        lines.append("")

    return "\n".join(lines).rstrip()


def format_ping(host: str, destination: str, replies: list[dict[str, str]], summary: list[str]) -> str:
    lines = [
        f"Pinging {host} [{destination or 'resolving...'}] with 56 bytes of data:",
        "",
    ]
    for reply in replies:
        lines.append(
            f"Reply from {reply['ip']}: bytes={reply['bytes']} time={reply['time']} TTL={reply['ttl']}"
        )
    if not replies:
        lines.append("No replies received.")
    if summary:
        lines.extend(["", *summary])
    return "\n".join(lines)


def format_traceroute(host: str, destination: str, hops: list[dict[str, str | list[str]]]) -> str:
    lines = [
        f"Tracing route to {host} [{destination or host}]",
        "over a maximum of 16 hops:",
        "",
    ]
    for hop in hops:
        if hop["status"] == "timeout":
            lines.append(f"{str(hop['hop']).rjust(3)}    *        *        *     Request timed out.")
            continue
        rtts = list(hop["rtts"])
        padded = [value.rjust(7) for value in (rtts + ["*"] * 3)[:3]]
        lines.append(f"{str(hop['hop']).rjust(3)} {''.join(padded)}  {hop['target']}")
    return "\n".join(lines)


def format_netstat(entries: list[dict[str, str]]) -> str:
    lines = [
        "Active Connections",
        "",
        "  Proto    Local Address               Foreign Address             State",
    ]
    for entry in entries:
        lines.append(
            f"  {entry['proto'].ljust(8)} {entry['local'].ljust(27)} {entry['remote'].ljust(27)} {entry['state']}"
        )
    if len(lines) == 3:
        lines.append("  No active TCP/UDP internet connections were found.")
    return "\n".join(lines)


def format_arp(entries: list[dict[str, str]]) -> str:
    lines = [
        "Interface: Address Resolution Cache",
        "",
        "  Internet Address     Physical Address       Type        Interface",
    ]
    for entry in entries:
        lines.append(
            f"  {entry['ip'].ljust(20)} {entry['mac'].ljust(22)} {entry['type'].ljust(11)} {entry['interface']}"
        )
    if len(lines) == 3:
        lines.append("  No ARP entries were found.")
    return "\n".join(lines)


def format_route_table(entries: list[dict[str, str]]) -> str:
    lines = [
        "IPv4 Route Table",
        "",
        "  Network Destination   Gateway              Interface   Flags",
    ]
    for entry in entries:
        lines.append(
            f"  {entry['destination'].ljust(21)} {entry['gateway'].ljust(20)} {entry['interface'].ljust(11)} {entry['flags']}"
        )
    if len(lines) == 3:
        lines.append("  No IPv4 routes were found.")
    return "\n".join(lines)


def format_getmac(entries: list[dict[str, str]]) -> str:
    lines = [
        "Physical Address      Transport Name   Adapter",
        "",
    ]
    for entry in entries:
        lines.append(
            f"{entry['physical_address'].ljust(21)} {entry['transport'].ljust(16)} {entry['adapter']}"
        )
    if len(lines) == 2:
        lines.append("No MAC addresses were found.")
    return "\n".join(lines)


def format_tasklist(entries: list[dict[str, str]], title: str = "Task List") -> str:
    lines = [
        title,
        "",
        "Image Name                 PID        CPU %      MEM %",
    ]
    for entry in entries:
        lines.append(
            f"{entry['image'][:24].ljust(25)} {entry['pid'].rjust(7)} {entry['cpu'].rjust(11)} {entry['memory'].rjust(10)}"
        )
    if len(lines) == 3:
        lines.append("No processes were found.")
    return "\n".join(lines)


def format_resolution(host: str, result: dict[str, object]) -> str:
    lines = [
        f"Resolution Summary for {host}",
        "",
        f"Canonical Name : {result.get('canonical_name') or 'Unavailable'}",
        f"IPv4 Addresses : {', '.join(result.get('ipv4', [])) or 'Unavailable'}",
        f"IPv6 Addresses : {', '.join(result.get('ipv6', [])) or 'Unavailable'}",
        f"Reverse Lookup : {', '.join(result.get('reverse', [])) or 'Unavailable'}",
    ]
    dig_lines = result.get("dig", [])
    if dig_lines:
        lines.append(f"dig +short    : {', '.join(dig_lines)}")
    errors = result.get("errors", [])
    if errors:
        lines.extend(["", "Errors:"])
        lines.extend(f"  {error}" for error in errors)
    nslookup_output = str(result.get("nslookup", "")).strip()
    if nslookup_output:
        lines.extend(["", "nslookup:", nslookup_output])
    return "\n".join(lines)


def format_socket_probe(title: str, result: dict[str, object]) -> str:
    status = "Success" if result.get("success") else "Failed"
    rows = [
        ("ComputerName", str(result.get("host", ""))),
        ("RemotePort", str(result.get("port", ""))),
        ("ResolvedAddress", str(result.get("resolved", "")) or "Unavailable"),
        ("Status", status),
        ("Latency", f"{result['latency_ms']} ms" if result.get("latency_ms") else "Unavailable"),
        ("Error", str(result.get("error", "")) or "None"),
    ]
    return "\n".join([title, "", *_rows(rows, indent=0)])


def format_simple_section(title: str, body: str) -> str:
    return "\n".join([title, "", body.strip() or "No data available."])


def format_geoip(result: dict[str, object]) -> str:
    rows = [
        ("Target", str(result.get("target", ""))),
        ("Resolved Address", str(result.get("resolved", "")) or "Unavailable"),
        ("Canonical Name", str(result.get("canonical_name", "")) or "Unavailable"),
        ("Reverse Name", str(result.get("reverse_name", "")) or "Unavailable"),
        ("Scope", str(result.get("scope", "")) or "Unavailable"),
        ("Country", str(result.get("country", "")) or "Unavailable"),
        ("Region", str(result.get("region", "")) or "Unavailable"),
        ("City", str(result.get("city", "")) or "Unavailable"),
        ("Coordinates", str(result.get("coordinates", "")) or "Unavailable"),
        ("Timezone", str(result.get("timezone", "")) or "Unavailable"),
        ("ISP", str(result.get("isp", "")) or "Unavailable"),
        ("Organization", str(result.get("org", "")) or "Unavailable"),
        ("ASN", str(result.get("asn", "")) or "Unavailable"),
    ]
    lines = ["IP Geolocation", "", *_rows(rows, indent=0)]
    note = str(result.get("note", "")).strip()
    if note:
        lines.extend(["", f"Note: {note}"])
    map_links = result.get("map_links") or {}
    if map_links:
        lines.extend(["", "Map Links:"])
        for label, url in map_links.items():
            lines.append(f"  {label}: {url}")
    return "\n".join(lines)


def format_neighbors(entries: list[dict[str, str]]) -> str:
    lines = [
        "Neighbor Devices",
        "",
        "  IP Address         Host Name                      MAC Address           Interface   Scope",
    ]
    for entry in entries:
        lines.append(
            f"  {entry['ip'].ljust(18)} {entry['hostname'][:28].ljust(30)} {entry['mac'].ljust(21)} {entry['interface'].ljust(11)} {entry['scope']}"
        )
    if len(lines) == 3:
        lines.append("  No neighboring devices were found in the ARP cache.")
    return "\n".join(lines)


def format_deviceinfo_local(system: SystemSnapshot, network: NetworkSnapshot) -> str:
    lines = [
        "Local Device Profile",
        "",
        *_rows(
            [
                ("Host Name", system.host_name),
                ("User Name", system.user_name),
                ("Architecture", system.architecture),
                ("Processor", system.processor),
                ("Memory", system.memory),
                ("OS Version", f"{system.os_name} {system.os_version} ({system.os_build})"),
                ("Default Gateway", network.default_gateway or "Unavailable"),
                ("DNS Servers", ", ".join(network.dns_servers) or "Unavailable"),
            ],
            indent=0,
        ),
        "",
        "Adapters:",
    ]
    for adapter in network.adapters:
        lines.append(f"  {adapter.name} [{adapter.device}]")
        lines.extend(
            [
                f"    IPv4: {adapter.ipv4 or 'Unavailable'}",
                f"    MAC : {adapter.mac.replace(':', '-').upper() if adapter.mac else 'Unavailable'}",
                f"    State: {adapter.media or adapter.status.title()}",
            ]
        )
    return "\n".join(lines)


def format_deviceinfo_target(result: dict[str, object]) -> str:
    rows = [
        ("Target", str(result.get("target", ""))),
        ("Resolved Address", str(result.get("resolved", "")) or "Unavailable"),
        ("Canonical Name", str(result.get("canonical_name", "")) or "Unavailable"),
        ("Reverse Name", str(result.get("reverse_name", "")) or "Unavailable"),
        ("Scope", str(result.get("scope", "")) or "Unavailable"),
        ("MAC Address", str(result.get("mac", "")) or "Unavailable"),
        ("Interface", str(result.get("interface", "")) or "Unavailable"),
        ("Adapter", str(result.get("adapter_name", "")) or "Unavailable"),
        (
            "Architecture",
            "Local device" if result.get("is_local") else "Unknown for remote target",
        ),
    ]
    lines = ["Target Device Profile", "", *_rows(rows, indent=0)]
    note = str(result.get("architecture_note", "")).strip()
    if note and not result.get("is_local"):
        lines.extend(["", f"Note: {note}"])
    geo = result.get("geo")
    if isinstance(geo, dict):
        lines.extend(
            [
                "",
                "Location:",
                f"  {geo.get('city', 'Unavailable')}, {geo.get('region', 'Unavailable')}, {geo.get('country', 'Unavailable')}",
                f"  Coordinates: {geo.get('coordinates', 'Unavailable')}",
            ]
        )
        map_links = geo.get("map_links") or {}
        if map_links:
            lines.append("  Map Links:")
            for label, url in map_links.items():
                lines.append(f"    {label}: {url}")
    elif result.get("geo_error"):
        lines.extend(["", f"Location lookup unavailable: {result['geo_error']}"])
    return "\n".join(lines)


def format_systeminfo(snapshot: SystemSnapshot) -> str:
    rows = [
        ("Host Name", snapshot.host_name),
        ("User Name", snapshot.user_name),
        ("OS Name", snapshot.os_name),
        ("OS Version", f"{snapshot.os_version} (Build {snapshot.os_build})"),
        ("Kernel Version", snapshot.kernel_version),
        ("System Type", snapshot.architecture),
        ("Processor", snapshot.processor),
        ("Total Physical Memory", snapshot.memory),
        ("System Uptime", snapshot.uptime),
    ]
    return "\n".join(["Host Name / OS Information", "", *_rows(rows, indent=0)])
