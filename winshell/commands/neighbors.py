from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_neighbors
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if cmd.args or cmd.flags:
        return CommandResponse(lines=["Usage: neighbors"])
    result = network.neighbor_devices()
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    return CommandResponse(lines=[format_neighbors(list(result.get("entries", [])))])


COMMANDS = [
    CommandSpec(
        "neighbors",
        "List nearby discovered devices with IP, MAC, and reverse DNS.",
        "neighbors",
        handle,
        aliases=("devices",),
        examples=("neighbors",),
    )
]
