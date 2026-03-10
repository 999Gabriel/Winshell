from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    return CommandResponse(lines=[network.get_whoami()])


COMMANDS = [
    CommandSpec("whoami", "Show the current signed-in user.", "whoami", handle, examples=("whoami",))
]
