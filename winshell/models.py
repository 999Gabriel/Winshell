from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ParsedCommand:
    raw: str
    name: str
    args: List[str]
    flags: Dict[str, str | bool]
    tokens: List[str] = field(default_factory=list)

    def has_flag(self, *names: str) -> bool:
        return any(name.lower() in self.flags for name in names)

    def flag_value(self, *names: str) -> str | None:
        for name in names:
            value = self.flags.get(name.lower())
            if isinstance(value, str):
                return value
        return None


@dataclass
class CommandResponse:
    lines: List[str] = field(default_factory=list)
    clear: bool = False
    exit_requested: bool = False
    mode: str | None = None
    export_path: str | None = None
    clipboard_target: str | None = None


@dataclass
class NetworkAdapter:
    device: str
    name: str
    mac: str = ""
    ipv4: str = ""
    subnet_mask: str = ""
    broadcast: str = ""
    ipv6: List[str] = field(default_factory=list)
    status: str = "unknown"
    media: str = ""
    mtu: str = ""
    is_default: bool = False


@dataclass
class NetworkSnapshot:
    host_name: str
    adapters: List[NetworkAdapter] = field(default_factory=list)
    default_gateway: str = ""
    default_interface: str = ""
    dns_servers: List[str] = field(default_factory=list)


@dataclass
class SystemSnapshot:
    host_name: str
    user_name: str
    os_name: str
    os_version: str
    os_build: str
    kernel_version: str
    architecture: str
    uptime: str
    processor: str
    memory: str
