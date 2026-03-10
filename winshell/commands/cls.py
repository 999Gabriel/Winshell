from __future__ import annotations

from winshell.commands.base import CommandSpec
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    return CommandResponse(clear=True)


COMMANDS = [
    CommandSpec("cls", "Clear the output window.", "cls", handle, aliases=("clear",), examples=("cls",))
]
