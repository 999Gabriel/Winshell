from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_route_table, format_unsupported
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if cmd.flags:
        return CommandResponse(lines=[format_unsupported()])
    if cmd.args and [arg.lower() for arg in cmd.args] != ["print"]:
        return CommandResponse(lines=[format_unsupported()])
    result = network.route_table()
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    return CommandResponse(lines=[format_route_table(list(result.get("entries", [])))])


COMMANDS = [
    CommandSpec(
        "route",
        "Show the IPv4 route table in a Windows-like layout.",
        "route print",
        handle,
        examples=("route print",),
    )
]
