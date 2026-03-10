from __future__ import annotations

import re
from textwrap import indent


def _kv(key: str, value: str) -> str:
    return f"{key:<32} : {value}"


def format_banner() -> str:
    return (
        "Microsoft Windows [Version 10.0.22631.1]\n"
        "(c) Microsoft Corporation. All rights reserved.\n\n"
        "WinShell for macOS - NWES Lab Edition\n"
        "Type 'help' to list available commands."
    )


def format_help() -> str:
    return """Supported commands:
  ipconfig
  ipconfig /all
  ping <host>
  tracert <host>
  netstat
  arp -a
  nslookup <host>
  hostname
  whoami
  systeminfo
  cls
  help
  exit

Examples:
  ipconfig /all
  ping 8.8.8.8
  tracert school.example.local
  nslookup nwes.local
"""


def format_unknown(cmd: str) -> str:
    return f"'{cmd}' is not recognized as an internal or external command,\noperable program or batch file."


def format_ipconfig_basic(data: dict) -> str:
    lines = ["Windows IP Configuration", ""]
    for iface in data.get("interfaces", []):
        lines.append(f"Ethernet adapter {iface['name']}:")
        lines.append(_kv("Connection-specific DNS Suffix", ""))
        lines.append(_kv("IPv4 Address", iface.get("ipv4", "")))
        lines.append(_kv("IPv6 Address", iface.get("ipv6", "")))
        lines.append(_kv("Physical Address", iface.get("mac", "")))
        lines.append(_kv("Media State", iface.get("status", "Disconnected")))
        lines.append("")
    return "\n".join(lines)


def format_ipconfig_all(data: dict) -> str:
    text = [format_ipconfig_basic(data)]
    text.append("DNS Details")
    text.append("-" * 60)
    dns = data.get("dns", "")
    dns_lines = [line for line in dns.splitlines() if "nameserver" in line.lower()][:8]
    text.extend(dns_lines or ["No DNS servers parsed."])
    text.append("")

    route = data.get("default_route", "")
    text.append("Default Gateway")
    text.append("-" * 60)
    m = re.search(r"gateway: (.+)", route)
    text.append(m.group(1).strip() if m else "Unknown")
    return "\n".join(text)


def format_tracert(raw: str, host: str) -> str:
    lines = [f"Tracing route to {host} over a maximum of 15 hops", ""]
    for line in raw.splitlines()[1:]:
        if line.strip():
            lines.append(line)
    lines.append("\nTrace complete.")
    return "\n".join(lines)


def format_systeminfo(data: dict) -> str:
    out = [
        _kv("Host Name", data.get("host", "")),
        _kv("OS Name", "macOS (Windows-style view)"),
        _kv("OS Version", " ".join(data.get("os", "").splitlines())),
        _kv("System Type", data.get("arch", "")),
        _kv("Processor", data.get("cpu", "")),
        _kv("Total Physical Memory", data.get("memory", "")),
        _kv("Kernel", data.get("kernel", "")),
        _kv("Python Runtime", data.get("python", "")),
        _kv("Snapshot Time", data.get("timestamp", "")),
        "",
        "Hardware Detail (trimmed):",
        indent("\n".join(data.get("hardware_blob", "").splitlines()[:20]), "  "),
    ]
    return "\n".join(out)
