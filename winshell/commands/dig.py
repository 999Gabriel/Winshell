from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_simple_section
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if not cmd.args:
        return CommandResponse(lines=["Usage: dig <host>"])
    result = network.dig_query(cmd.args)
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    return CommandResponse(lines=[format_simple_section("dig", str(result["output"]))])


COMMANDS = [
    CommandSpec("dig", "Run a dig lookup and show the raw response.", "dig <host>", handle, examples=("dig openai.com",))
]
