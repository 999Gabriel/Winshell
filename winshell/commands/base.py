from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from winshell.models import CommandResponse, ParsedCommand

CommandHandler = Callable[[ParsedCommand, str, Any], CommandResponse]


@dataclass(frozen=True)
class CommandSpec:
    name: str
    summary: str
    usage: str
    handler: CommandHandler
    aliases: tuple[str, ...] = field(default_factory=tuple)
    examples: tuple[str, ...] = field(default_factory=tuple)
    permission_level: str = "normal"
