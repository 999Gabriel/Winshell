from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_traceroute
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if not cmd.args:
        return CommandResponse(lines=["Usage: tracert <host>"])
    result = network.traceroute_host(cmd.args[0])
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    return CommandResponse(
        lines=[format_traceroute(cmd.args[0], str(result.get("destination", "")), list(result.get("hops", [])))]
    )


COMMANDS = [
    CommandSpec(
        "tracert",
        "Trace the route to a remote host.",
        "tracert <host>",
        handle,
        examples=("tracert example.com",),
    )
]
