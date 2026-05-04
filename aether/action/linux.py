from __future__ import annotations

from aether.action.base import ActionAdapter


class LinuxActionAdapter(ActionAdapter):
    def click(self, x: int, y: int) -> None:
        pass

    def type_text(self, text: str) -> None:
        pass

    def hotkey(self, modifiers: list[str], key: str) -> None:
        pass

    def scroll(self, x: int, y: int, delta: int) -> None:
        pass
