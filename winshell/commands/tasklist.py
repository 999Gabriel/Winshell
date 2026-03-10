from __future__ import annotations

from winshell.adapters import system
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_tasklist, format_unsupported
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if cmd.args or cmd.flags:
        return CommandResponse(lines=[format_unsupported()])
    title = "Get-Process" if cmd.name == "get-process" else "Task List"
    result = system.process_list()
    if "error" in result:
        return CommandResponse(lines=[f"Process listing is unavailable in this environment: {result['error']}"])
    return CommandResponse(lines=[format_tasklist(list(result.get("entries", [])), title=title)])


COMMANDS = [
    CommandSpec(
        "tasklist",
        "Show running processes with CPU and memory usage.",
        "tasklist",
        handle,
        aliases=("get-process",),
        examples=("tasklist", "get-process"),
    )
]
