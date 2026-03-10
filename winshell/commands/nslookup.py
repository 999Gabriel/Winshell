from __future__ import annotations

from winshell.adapters import network
from winshell.commands.base import CommandSpec
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    result = network.nslookup_query(cmd.args)
    if "error" in result:
        return CommandResponse(lines=[str(result["error"])])
    return CommandResponse(lines=[str(result["output"])])


COMMANDS = [
    CommandSpec(
        "nslookup",
        "Resolve DNS records for a host.",
        "nslookup <host>",
        handle,
        examples=("nslookup openai.com",),
    )
]
