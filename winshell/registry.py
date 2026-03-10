from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from winshell.adapters import network, system
from winshell.formatters.windows_style import (
    format_arp,
    format_help,
    format_ipconfig,
    format_netstat,
    format_ping,
    format_systeminfo,
    format_traceroute,
    format_unknown,
    format_unsupported,
)
from winshell.models import CommandResponse, ParsedCommand

CommandHandler = Callable[[ParsedCommand, str, "CommandRegistry"], CommandResponse]


@dataclass(frozen=True)
class CommandSpec:
    name: str
    summary: str
    usage: str
    handler: CommandHandler
    aliases: tuple[str, ...] = field(default_factory=tuple)


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, CommandSpec] = {}
        for spec in self._default_commands():
            self.register(spec)

    def _default_commands(self) -> list[CommandSpec]:
        return [
            CommandSpec("help", "Show supported commands and examples.", "help", self._handle_help, aliases=("?",)),
            CommandSpec("ipconfig", "Show Windows-style network adapter details.", "ipconfig [/all]", self._handle_ipconfig),
            CommandSpec("ping", "Ping a host using four probes by default.", "ping <host>", self._handle_ping),
            CommandSpec("tracert", "Trace the route to a remote host.", "tracert <host>", self._handle_tracert),
            CommandSpec("netstat", "Display active TCP and UDP connections.", "netstat", self._handle_netstat),
            CommandSpec("arp", "Display the ARP cache.", "arp -a", self._handle_arp),
            CommandSpec("nslookup", "Resolve DNS records for a host.", "nslookup <host>", self._handle_nslookup),
            CommandSpec("hostname", "Show the current host name.", "hostname", self._handle_hostname),
            CommandSpec("whoami", "Show the current signed-in user.", "whoami", self._handle_whoami),
            CommandSpec("systeminfo", "Show macOS system information in a Windows layout.", "systeminfo", self._handle_systeminfo),
            CommandSpec("cls", "Clear the output window.", "cls", self._handle_cls, aliases=("clear",)),
            CommandSpec("exit", "Exit WinShell.", "exit", self._handle_exit, aliases=("quit",)),
            CommandSpec("mode", "Switch between CMD and PowerShell prompts.", "mode <cmd|powershell>", self._handle_mode),
            CommandSpec("export", "Export the visible transcript to a text file.", "export <file>", self._handle_export),
        ]

    def register(self, spec: CommandSpec) -> None:
        self._commands[spec.name] = spec
        for alias in spec.aliases:
            self._commands[alias] = spec

    def command_rows(self) -> list[dict[str, str]]:
        unique = {spec.name: spec for spec in self._commands.values()}
        return [
            {"name": spec.name, "summary": spec.summary, "usage": spec.usage}
            for spec in sorted(unique.values(), key=lambda item: item.name)
        ]

    def command_names(self) -> list[str]:
        return sorted({spec.name for spec in self._commands.values()})

    def completions(self, prefix: str) -> list[str]:
        prefix = prefix.lower()
        return [name for name in self.command_names() if name.startswith(prefix)]

    def execute(self, cmd: ParsedCommand, mode: str) -> CommandResponse:
        if not cmd.name:
            return CommandResponse()
        spec = self._commands.get(cmd.name)
        if spec is None:
            return CommandResponse(lines=[format_unknown(cmd.name)])
        return spec.handler(cmd, mode, self)

    def _handle_help(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        return CommandResponse(lines=[format_help(self.command_rows())])

    def _handle_ipconfig(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        if cmd.args or set(cmd.flags) - {"/all"}:
            return CommandResponse(lines=[format_unsupported()])
        return CommandResponse(lines=[format_ipconfig(network.network_snapshot(), detailed=cmd.has_flag("/all"))])

    def _handle_ping(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
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

    def _handle_tracert(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        if not cmd.args:
            return CommandResponse(lines=["Usage: tracert <host>"])
        result = network.traceroute_host(cmd.args[0])
        if "error" in result:
            return CommandResponse(lines=[str(result["error"])])
        return CommandResponse(
            lines=[format_traceroute(cmd.args[0], str(result.get("destination", "")), list(result.get("hops", [])))]
        )

    def _handle_netstat(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        result = network.netstat_connections(cmd.flags)
        if result.get("unsupported"):
            return CommandResponse(lines=[format_unsupported()])
        if "error" in result:
            return CommandResponse(lines=[str(result["error"])])
        return CommandResponse(lines=[format_netstat(list(result.get("entries", [])))])

    def _handle_arp(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        if cmd.args or set(cmd.flags) - {"-a"}:
            return CommandResponse(lines=[format_unsupported()])
        result = network.arp_cache()
        if "error" in result:
            return CommandResponse(lines=[str(result["error"])])
        return CommandResponse(lines=[format_arp(list(result.get("entries", [])))])

    def _handle_nslookup(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        result = network.nslookup_query(cmd.args)
        if "error" in result:
            return CommandResponse(lines=[str(result["error"])])
        return CommandResponse(lines=[str(result["output"])])

    def _handle_hostname(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        return CommandResponse(lines=[network.get_hostname()])

    def _handle_whoami(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        return CommandResponse(lines=[network.get_whoami()])

    def _handle_systeminfo(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        if cmd.args or cmd.flags:
            return CommandResponse(lines=[format_unsupported()])
        return CommandResponse(lines=[format_systeminfo(system.system_snapshot())])

    def _handle_cls(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        return CommandResponse(clear=True)

    def _handle_exit(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        return CommandResponse(exit_requested=True)

    def _handle_mode(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        if not cmd.args:
            label = "PowerShell" if mode == "powershell" else "CMD"
            return CommandResponse(lines=[f"Current mode: {label}"])
        requested = cmd.args[0].lower()
        if requested not in {"cmd", "powershell"}:
            return CommandResponse(lines=["Usage: mode <cmd|powershell>"])
        label = "CMD" if requested == "cmd" else "PowerShell"
        return CommandResponse(lines=[f"Switched to {label} mode."], mode=requested)

    def _handle_export(self, cmd: ParsedCommand, mode: str, registry: "CommandRegistry") -> CommandResponse:
        if len(cmd.args) != 1:
            return CommandResponse(lines=["Usage: export <file>"])
        return CommandResponse(export_path=cmd.args[0])
