from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Input, RichLog, Static

from winshell.formatters.windows_style import format_banner
from winshell.parser import CommandParser
from winshell.registry import CommandRegistry


class WinShellApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #title {
        height: auto;
        padding: 0 1;
        color: cyan;
    }
    #output {
        height: 1fr;
        border: round #666666;
    }
    #prompt {
        dock: bottom;
    }
    """

    BINDINGS = [
        ("up", "history_up", "History up"),
        ("down", "history_down", "History down"),
        ("ctrl+l", "clear", "Clear"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.parser = CommandParser()
        self.registry = CommandRegistry()
        self.history: list[str] = []
        self.history_idx = -1

    def compose(self) -> ComposeResult:
        yield Header(name="WinShell")
        yield Static("NWES Windows-like Admin Console (macOS)", id="title")
        with Vertical():
            yield RichLog(id="output", wrap=True, highlight=False, markup=False)
            yield Input(placeholder="C:\\>", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        out = self.query_one("#output", RichLog)
        out.write(format_banner())
        self.query_one("#prompt", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        input_widget = self.query_one("#prompt", Input)
        input_widget.value = ""

        if not command:
            return

        self.history.append(command)
        self.history_idx = len(self.history)

        out = self.query_one("#output", RichLog)
        out.write(f"\nC:\\> {command}")

        parsed = self.parser.parse(command)
        result, should_exit, should_clear = self.registry.execute(parsed)

        if should_clear:
            out.clear()
            return

        if result:
            out.write(result)

        if should_exit:
            self.exit()

    def action_history_up(self) -> None:
        if not self.history:
            return
        self.history_idx = max(0, self.history_idx - 1)
        self.query_one("#prompt", Input).value = self.history[self.history_idx]

    def action_history_down(self) -> None:
        if not self.history:
            return
        self.history_idx = min(len(self.history), self.history_idx + 1)
        prompt = self.query_one("#prompt", Input)
        prompt.value = "" if self.history_idx == len(self.history) else self.history[self.history_idx]

    def action_clear(self) -> None:
        self.query_one("#output", RichLog).clear()


def run() -> None:
    WinShellApp().run()
