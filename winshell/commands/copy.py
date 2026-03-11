from __future__ import annotations

from winshell.commands.base import CommandSpec
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if len(cmd.args) > 1:
        return CommandResponse(lines=["Usage: copy [all|last]"])

    target = "all"
    if cmd.args:
        target = cmd.args[0].lower()
        if target not in {"all", "last"}:
            return CommandResponse(lines=["Usage: copy [all|last]"])

    return CommandResponse(clipboard_target=target)


COMMANDS = [
    CommandSpec(
        "copy",
        "Copy visible output to the macOS clipboard.",
        "copy [all|last]",
        handle,
        aliases=("clip",),
        examples=("copy", "copy all", "copy last"),
    )
]
