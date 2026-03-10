from __future__ import annotations

from pathlib import Path

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
        lines.append(f"  {row['name'].ljust(14)} {row['summary']}")
    lines.extend(
        [
            "",
            "Examples:",
            "  ipconfig",
            "  ipconfig /all",
            "  ping example.com",
            "  tracert example.com",
            "  nslookup openai.com",
            "  systeminfo",
            "  mode cmd",
            "  export winshell-output.txt",
        ]
    )
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
