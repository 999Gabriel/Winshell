from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_ipconfig, format_unsupported
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if cmd.args or set(cmd.flags) - {"/all"}:
        return CommandResponse(lines=[format_unsupported()])
    return CommandResponse(lines=[format_ipconfig(network.network_snapshot(), detailed=cmd.has_flag("/all"))])


COMMANDS = [
    CommandSpec(
        "ipconfig",
        "Show Windows-style network adapter details.",
        "ipconfig [/all]",
        handle,
        examples=("ipconfig", "ipconfig /all"),
    )
]
