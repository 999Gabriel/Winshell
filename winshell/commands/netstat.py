from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_netstat, format_unsupported
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    result = network.netstat_connections(cmd.flags)
    if result.get("unsupported"):
        return CommandResponse(lines=[format_unsupported()])
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    return CommandResponse(lines=[format_netstat(list(result.get("entries", [])))])


COMMANDS = [
    CommandSpec(
        "netstat",
        "Display active TCP and UDP connections.",
        "netstat [-a|-n|-an]",
        handle,
        examples=("netstat", "netstat -an"),
    )
]
