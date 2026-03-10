from __future__ import annotations

from winshell.commands.base import CommandSpec
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if len(cmd.args) != 1:
        return CommandResponse(lines=["Usage: export <file>"])
    return CommandResponse(export_path=cmd.args[0])


COMMANDS = [
    CommandSpec(
        "export",
        "Export the visible transcript to a text file.",
        "export <file>",
        handle,
        examples=("export winshell-output.txt",),
    )
]
