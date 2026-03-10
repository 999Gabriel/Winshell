from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_ping
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if not cmd.args:
        return CommandResponse(lines=["Usage: ping <host>"])
    count_raw = cmd.flag_value("-n", "-c")
    count = int(count_raw) if count_raw and count_raw.isdigit() else 4
    result = network.ping_host(cmd.args[0], count=count)
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    return CommandResponse(
        lines=[
            format_ping(
                cmd.args[0],
                str(result.get("destination", "")),
                list(result.get("replies", [])),
                list(result.get("summary", [])),
            )
        ]
    )


COMMANDS = [
    CommandSpec(
        "ping",
        "Ping a host using four probes by default.",
        "ping <host> [-n count]",
        handle,
        examples=("ping example.com", "ping 8.8.8.8 -n 2"),
    )
]
