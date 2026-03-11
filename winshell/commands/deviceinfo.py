from __future__ import annotations

from winshell.adapters import network, system
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_deviceinfo_local, format_deviceinfo_target
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if not cmd.args:
        return CommandResponse(
            lines=[format_deviceinfo_local(system.system_snapshot(), network.network_snapshot())]
        )
    if len(cmd.args) != 1:
        return CommandResponse(lines=["Usage: deviceinfo [ip-or-host]"])
    result = network.inspect_target(cmd.args[0])
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    if result.get("is_local"):
        return CommandResponse(
            lines=[format_deviceinfo_local(system.system_snapshot(), network.network_snapshot())]
        )
    return CommandResponse(lines=[format_deviceinfo_target(result)])


COMMANDS = [
    CommandSpec(
        "deviceinfo",
        "Inspect the local Mac or a target host with IP, MAC, and location context.",
        "deviceinfo [ip-or-host]",
        handle,
        aliases=("inspect",),
        examples=("deviceinfo", "deviceinfo localhost", "deviceinfo 8.8.8.8"),
    )
]
