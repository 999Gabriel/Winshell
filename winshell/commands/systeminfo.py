from __future__ import annotations

from winshell.adapters import system
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_systeminfo, format_unsupported
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if cmd.args or cmd.flags:
        return CommandResponse(lines=[format_unsupported()])
    return CommandResponse(lines=[format_systeminfo(system.system_snapshot())])


COMMANDS = [
    CommandSpec(
        "systeminfo",
        "Show macOS system information in a Windows layout.",
        "systeminfo",
        handle,
        examples=("systeminfo",),
    )
]
