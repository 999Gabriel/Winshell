from __future__ import annotations

from winshell.commands import load_command_specs
from winshell.commands.base import CommandSpec
from winshell.formatters.windows_style import format_unknown
from winshell.models import CommandResponse, ParsedCommand


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, CommandSpec] = {}
        self._primary_commands: dict[str, CommandSpec] = {}
        for spec in load_command_specs():
            self.register(spec)

    def register(self, spec: CommandSpec) -> None:
        self._primary_commands[spec.name] = spec
        self._commands[spec.name] = spec
        for alias in spec.aliases:
            self._commands[alias] = spec

    def execute(self, cmd: ParsedCommand, mode: str) -> CommandResponse:
        if not cmd.name:
            return CommandResponse()
        spec = self._commands.get(cmd.name)
        if spec is None:
            return CommandResponse(lines=[format_unknown(cmd.name)])
        return spec.handler(cmd, mode, self)

    def completions(self, prefix: str) -> list[str]:
        prefix = prefix.lower()
        return sorted(name for name in self._commands if name.startswith(prefix))

    def command_rows(self) -> list[dict[str, str]]:
        return [
            {
                "name": spec.name,
                "summary": spec.summary,
                "usage": spec.usage,
                "permission_level": spec.permission_level,
                "examples": ", ".join(spec.examples),
                "aliases": ", ".join(spec.aliases),
            }
            for spec in sorted(self._primary_commands.values(), key=lambda item: item.name)
        ]

    def get_command(self, name: str) -> CommandSpec | None:
        return self._commands.get(name.lower())
