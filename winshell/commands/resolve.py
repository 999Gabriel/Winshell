from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_resolution
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if not cmd.args:
        return CommandResponse(lines=["Usage: resolve <host>"])
    result = network.resolve_host(cmd.args[0])
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    return CommandResponse(lines=[format_resolution(cmd.args[0], result)])


COMMANDS = [
    CommandSpec(
        "resolve",
        "Show a combined dig, lookup, and reverse-DNS summary.",
        "resolve <host>",
        handle,
        examples=("resolve openai.com",),
    )
]
