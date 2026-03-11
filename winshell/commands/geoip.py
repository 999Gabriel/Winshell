from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_geoip
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if len(cmd.args) != 1:
        return CommandResponse(lines=["Usage: geoip <ip-or-host>"])
    result = network.geoip_lookup(cmd.args[0])
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    return CommandResponse(lines=[format_geoip(result)])


COMMANDS = [
    CommandSpec(
        "geoip",
        "Show public-IP geolocation with coordinates and map links.",
        "geoip <ip-or-host>",
        handle,
        aliases=("whereisip",),
        examples=("geoip 8.8.8.8", "geoip example.com"),
    )
]
