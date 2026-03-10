from __future__ import annotations

from typing import Callable

from textual.widgets import Input


class CommandInput(Input):
    def __init__(self, completion_provider: Callable[[str], list[str]], **kwargs) -> None:
        super().__init__(**kwargs)
        self._completion_provider = completion_provider
        self._history: list[str] = []
        self._history_index: int | None = None
        self._completion_seed = ""
        self._completion_matches: list[str] = []
        self._completion_index = -1

    def add_history(self, command: str) -> None:
        command = command.strip()
        if not command:
            return
        if not self._history or self._history[-1] != command:
            self._history.append(command)
        self._history_index = None
        self._reset_completion()

    def _reset_completion(self) -> None:
        self._completion_seed = ""
        self._completion_matches = []
        self._completion_index = -1

    def action_history_prev(self) -> None:
        if not self._history:
            return
        if self._history_index is None:
            self._history_index = len(self._history) - 1
        elif self._history_index > 0:
            self._history_index -= 1
        self.value = self._history[self._history_index]
        self.cursor_position = len(self.value)

    def action_history_next(self) -> None:
        if self._history_index is None:
            return
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self.value = self._history[self._history_index]
        else:
            self._history_index = None
            self.value = ""
        self.cursor_position = len(self.value)

    def action_complete_command(self) -> None:
        seed = self.value.strip().lower()
        if not seed or " " in seed:
            return
        if seed != self._completion_seed:
            self._completion_seed = seed
            self._completion_matches = self._completion_provider(seed)
            self._completion_index = -1
        if not self._completion_matches:
            return
        self._completion_index = (self._completion_index + 1) % len(self._completion_matches)
        self.value = self._completion_matches[self._completion_index]
        self.cursor_position = len(self.value)

    async def key_up(self) -> None:
        self.action_history_prev()

    async def key_down(self) -> None:
        self.action_history_next()

    async def key_tab(self) -> None:
        self.action_complete_command()
