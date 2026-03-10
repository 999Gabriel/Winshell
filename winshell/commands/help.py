from __future__ import annotations

from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_command_help, format_help
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if cmd.args:
        spec = registry.get_command(cmd.args[0])
        if spec is None:
            return CommandResponse(lines=[f"No help entry exists for '{cmd.args[0]}'"])
        return CommandResponse(lines=[format_command_help(spec)])
    return CommandResponse(lines=[format_help(registry.command_rows())])


COMMANDS = [
    CommandSpec(
        "help",
        "Show supported commands and examples.",
        "help [command]",
        handle,
        aliases=("?",),
        examples=("help", "help route"),
    )
]
