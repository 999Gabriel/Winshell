from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    return CommandResponse(lines=[network.get_hostname()])


COMMANDS = [
    CommandSpec("hostname", "Show the current host name.", "hostname", handle, examples=("hostname",))
]
