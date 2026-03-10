from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_arp, format_unsupported
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if cmd.args or set(cmd.flags) - {"-a"}:
        return CommandResponse(lines=[format_unsupported()])
    result = network.arp_cache()
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    return CommandResponse(lines=[format_arp(list(result.get("entries", [])))])


COMMANDS = [
    CommandSpec(
        "arp",
        "Display the ARP cache.",
        "arp -a",
        handle,
        examples=("arp -a",),
    )
]
