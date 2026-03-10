from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_getmac, format_unsupported
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if cmd.args or cmd.flags:
        return CommandResponse(lines=[format_unsupported()])
    return CommandResponse(lines=[format_getmac(network.mac_addresses())])


COMMANDS = [
    CommandSpec(
        "getmac",
        "List adapter MAC addresses in a Windows-style table.",
        "getmac",
        handle,
        examples=("getmac",),
    )
]
