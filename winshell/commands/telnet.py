from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_socket_probe
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if len(cmd.args) != 2 or not cmd.args[1].isdigit():
        return CommandResponse(lines=["Usage: telnet <host> <port>"])
    result = network.tcp_probe(cmd.args[0], int(cmd.args[1]))
    return CommandResponse(lines=[format_socket_probe("Telnet Emulation", result)])


COMMANDS = [
    CommandSpec(
        "telnet",
        "Attempt a TCP connection to a host and port.",
        "telnet <host> <port>",
        handle,
        examples=("telnet example.com 443",),
    )
]
