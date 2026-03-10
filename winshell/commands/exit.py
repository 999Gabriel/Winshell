from __future__ import annotations

from winshell.commands.base import CommandSpec
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    return CommandResponse(exit_requested=True)


COMMANDS = [
    CommandSpec("exit", "Exit WinShell.", "exit", handle, aliases=("quit",), examples=("exit",))
]
