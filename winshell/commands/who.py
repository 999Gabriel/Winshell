from __future__ import annotations

from winshell.adapters import system
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_simple_section
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    return CommandResponse(lines=[format_simple_section("Logged-In Users", system.who_output())])


COMMANDS = [
    CommandSpec("who", "List currently logged-in users.", "who", handle, examples=("who",))
]
