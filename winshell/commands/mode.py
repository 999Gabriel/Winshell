from __future__ import annotations

from winshell.commands.base import CommandSpec
from winshell.models import CommandResponse, ParsedCommand


def handle(cmd: ParsedCommand, mode: str, registry: object) -> CommandResponse:
    if not cmd.args:
        label = "PowerShell" if mode == "powershell" else "CMD"
        return CommandResponse(lines=[f"Current mode: {label}"])
    requested = cmd.args[0].lower()
    if requested not in {"cmd", "powershell"}:
        return CommandResponse(lines=["Usage: mode <cmd|powershell>"])
    label = "CMD" if requested == "cmd" else "PowerShell"
    return CommandResponse(lines=[f"Switched to {label} mode."], mode=requested)


COMMANDS = [
    CommandSpec(
        "mode",
        "Switch between CMD and PowerShell prompts.",
        "mode <cmd|powershell>",
        handle,
        examples=("mode cmd", "mode powershell"),
    )
]
