from __future__ import annotations

import asyncio
from pathlib import Path
import subprocess

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Input, RichLog, Static

from winshell.formatters.windows_style import format_banner
from winshell.parser import CommandParser
from winshell.registry import CommandRegistry
from winshell.widgets.command_input import CommandInput


class WinShellApp(App[None]):
    CSS = """
    Screen {
        background: #111827;
        color: #e5e7eb;
    }

    #header-bar {
        background: #0f3d2e;
        color: #f8fafc;
        padding: 0 1;
        height: 1;
    }

    #status-bar {
        background: #1f2937;
        color: #93c5fd;
        padding: 0 1;
        height: 1;
    }

    #console {
        height: 1fr;
    }

    #output {
        border: round #334155;
        background: #020617;
        color: #dbeafe;
        padding: 1;
    }

    #input-row {
        height: 3;
        padding: 0 1;
        background: #0f172a;
    }

    #prompt-label {
        width: 8;
        content-align: center middle;
        color: #fbbf24;
    }

    #prompt {
        width: 1fr;
        border: round #475569;
    }

    .cmd-mode #header-bar {
        background: #3f3f46;
    }

    .cmd-mode #status-bar {
        color: #facc15;
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "clear_console", "Clear"),
        Binding("f6", "copy_visible_output", "Copy Output"),
        Binding("f2", "toggle_mode", "Toggle Mode"),
        Binding("ctrl+d", "quit", "Exit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.cwd = Path.cwd()
        self.shell_mode = "powershell"
        self.parser = CommandParser()
        self.registry = CommandRegistry()
        self.transcript: list[str] = []
        self.last_output: str = ""

    def compose(self) -> ComposeResult:
        yield Static(id="header-bar")
        yield Static(id="status-bar")
        with Container(id="console"):
            yield RichLog(id="output", wrap=True, highlight=False, markup=False, auto_scroll=True)
        with Horizontal(id="input-row"):
            yield Static(id="prompt-label")
            yield CommandInput(
                id="prompt",
                placeholder="Enter a WinShell command",
                completion_provider=self.registry.completions,
            )
        yield Footer()

    def on_mount(self) -> None:
        self._apply_mode()
        self._append_block(format_banner(self.shell_mode, self.cwd))
        self._append_block("")
        self._append_block("Type HELP to see supported commands.")
        self.query_one(CommandInput).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        event.input.value = ""
        if not raw:
            return

        prompt = self.query_one(CommandInput)
        prompt.add_history(raw)
        self._append_block(f"{self._prompt_text()} {raw}")

        parsed = self.parser.parse(raw)
        response = await asyncio.to_thread(self.registry.execute, parsed, self.shell_mode)

        if response.clear:
            self.action_clear_console()

        if response.mode:
            self.shell_mode = response.mode
            self._apply_mode()

        if response.export_path:
            export_message = self._export_transcript(response.export_path)
            self._append_block(export_message)
            self.last_output = export_message

        if response.clipboard_target:
            clipboard_message = self._copy_requested_output(response.clipboard_target)
            self._append_block(clipboard_message)

        rendered_blocks: list[str] = []
        for block in response.lines:
            if block:
                self._append_block(block)
                rendered_blocks.append(block)

        if rendered_blocks:
            self.last_output = "\n\n".join(rendered_blocks)

        if response.exit_requested:
            self.exit()

    def action_clear_console(self) -> None:
        self.transcript.clear()
        self.last_output = ""
        self.query_one(RichLog).clear()

    def action_copy_visible_output(self) -> None:
        self._append_block(self._copy_requested_output("all"))

    def action_toggle_mode(self) -> None:
        self.shell_mode = "cmd" if self.shell_mode == "powershell" else "powershell"
        self._apply_mode()
        self._append_block(f"Switched to {self._mode_label()} mode.")

    def _apply_mode(self) -> None:
        self.set_class(self.shell_mode == "cmd", "cmd-mode")
        self.query_one("#header-bar", Static).update(
            f"WinShell | {self._mode_label()} Mode | {self.cwd}"
        )
        self.query_one("#status-bar", Static).update(
            "Windows-like networking tools for macOS | HELP for commands | TAB to complete | F6 copy"
        )
        self.query_one("#prompt-label", Static).update(self._prompt_text())

    def _prompt_text(self) -> str:
        return "PS>" if self.shell_mode == "powershell" else "C:\\>"

    def _mode_label(self) -> str:
        return "PowerShell" if self.shell_mode == "powershell" else "CMD"

    def _append_block(self, text: str) -> None:
        self.transcript.append(text)
        output = self.query_one(RichLog)
        for line in text.splitlines() or [""]:
            output.write(line)

    def _export_transcript(self, raw_path: str) -> str:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = self.cwd / path
        path.write_text("\n\n".join(self.transcript).rstrip() + "\n", encoding="utf-8")
        return f"Transcript exported to {path}"

    def _copy_requested_output(self, target: str) -> str:
        if target == "last":
            text = self.last_output.strip()
            if not text:
                return "No previous command output is available to copy."
            return self._copy_to_clipboard(text, "Last output copied to clipboard.")

        text = "\n\n".join(self.transcript).rstrip()
        if not text:
            return "Nothing is available to copy."
        return self._copy_to_clipboard(text, "Visible output copied to clipboard.")

    def _copy_to_clipboard(self, text: str, success_message: str) -> str:
        try:
            process = subprocess.run(
                ["pbcopy"],
                input=text,
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            return f"Clipboard copy failed: {exc}"

        if process.returncode != 0:
            error_text = process.stderr.strip() or process.stdout.strip() or "pbcopy failed."
            return f"Clipboard copy failed: {error_text}"
        return success_message


def run() -> None:
    WinShellApp().run()
