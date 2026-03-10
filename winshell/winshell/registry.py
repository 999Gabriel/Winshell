from __future__ import annotations

from winshell.adapters import network, system
from winshell.formatters.windows_style import (
    format_help,
    format_ipconfig_all,
    format_ipconfig_basic,
    format_systeminfo,
    format_tracert,
    format_unknown,
)
from winshell.models import ParsedCommand


class CommandRegistry:
    def execute(self, cmd: ParsedCommand) -> tuple[str, bool, bool]:
        """Return: (output, should_exit, should_clear)."""
        if not cmd.name:
            return "", False, False

        if cmd.name == "help":
            return format_help(), False, False
        if cmd.name == "exit":
            return "Exiting WinShell...", True, False
        if cmd.name == "cls":
            return "", False, True

        if cmd.name == "ipconfig":
            if "/all" in cmd.flags:
                return format_ipconfig_all(network.ipconfig_all()), False, False
            return format_ipconfig_basic(network.ipconfig_basic()), False, False

        if cmd.name == "ping":
            if not cmd.args:
                return "Usage: ping <host>", False, False
            return network.do_ping(cmd.args[0]), False, False

        if cmd.name == "tracert":
            if not cmd.args:
                return "Usage: tracert <host>", False, False
            host = cmd.args[0]
            raw = network.do_tracert(host)
            return format_tracert(raw, host), False, False

        if cmd.name == "netstat":
            return network.do_netstat(), False, False

        if cmd.name == "arp" and cmd.args == ["-a"]:
            return network.do_arp_all(), False, False

        if cmd.name == "nslookup":
            if not cmd.args:
                return "Usage: nslookup <host>", False, False
            return network.do_nslookup(cmd.args[0]), False, False

        if cmd.name == "hostname":
            return network.get_hostname(), False, False

        if cmd.name == "whoami":
            return network.get_whoami(), False, False

        if cmd.name == "systeminfo":
            return format_systeminfo(system.get_systeminfo()), False, False

        return format_unknown(cmd.name), False, False
