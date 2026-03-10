from __future__ import annotations

import re
import socket
from typing import Dict, List

from winshell.adapters.runner import run_command


def get_hostname() -> str:
    return socket.gethostname()


def get_whoami() -> str:
    return run_command(["whoami"]).stdout.strip()


def ipconfig_basic() -> Dict[str, List[dict]]:
    result = run_command(["ifconfig"])
    interfaces = []
    blocks = re.split(r"\n(?=\S)", result.stdout.strip())
    for block in blocks:
        lines = block.splitlines()
        if not lines:
            continue
        first = lines[0]
        name = first.split(":", 1)[0]
        ipv4 = ""
        ipv6 = ""
        mac = ""
        status = "Disconnected"
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("inet "):
                parts = line.split()
                if len(parts) > 1:
                    ipv4 = parts[1]
            elif line.startswith("inet6 "):
                parts = line.split()
                if len(parts) > 1 and not parts[1].startswith("fe80"):
                    ipv6 = parts[1]
            elif line.startswith("ether "):
                parts = line.split()
                if len(parts) > 1:
                    mac = parts[1]
            if "status: active" in line:
                status = "Connected"

        if name.startswith("lo"):
            continue

        interfaces.append(
            {
                "name": name,
                "ipv4": ipv4,
                "ipv6": ipv6,
                "mac": mac,
                "status": status,
            }
        )

    return {"interfaces": interfaces}


def ipconfig_all() -> Dict[str, str | List[dict]]:
    basic = ipconfig_basic()
    dns = run_command(["scutil", "--dns"]).stdout
    route = run_command(["route", "-n", "get", "default"]).stdout
    return {"interfaces": basic["interfaces"], "dns": dns, "default_route": route}


def do_ping(host: str) -> str:
    return run_command(["ping", "-c", "4", host], timeout=20).stdout


def do_tracert(host: str) -> str:
    result = run_command(["traceroute", "-m", "15", host], timeout=40)
    return result.stdout if result.stdout else result.stderr


def do_netstat() -> str:
    return run_command(["netstat", "-rn"]).stdout


def do_arp_all() -> str:
    return run_command(["arp", "-a"]).stdout


def do_nslookup(host: str) -> str:
    result = run_command(["nslookup", host])
    return result.stdout if result.stdout else result.stderr
