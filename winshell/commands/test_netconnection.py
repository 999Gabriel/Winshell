from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_socket_probe
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if not cmd.args:
        return CommandResponse(lines=["Usage: test-netconnection <host> -port <n>"])

    host = cmd.args[0]
    port_raw = cmd.flag_value("-port", "/port", "-p")
    if port_raw is None and len(cmd.args) > 1:
        port_raw = cmd.args[1]
    if not port_raw or not str(port_raw).isdigit():
        return CommandResponse(lines=["Usage: test-netconnection <host> -port <n>"])

    result = network.tcp_probe(host, int(str(port_raw)))
    return CommandResponse(lines=[format_socket_probe("Test-NetConnection", result)])


COMMANDS = [
    CommandSpec(
        "test-netconnection",
        "PowerShell-style TCP connectivity test.",
        "test-netconnection <host> -port <n>",
        handle,
        aliases=("tnc",),
        examples=("test-netconnection example.com -port 443", "tnc localhost -port 22"),
    )
]
