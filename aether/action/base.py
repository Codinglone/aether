from __future__ import annotations

from abc import ABC, abstractmethod


class ActionAdapter(ABC):
    @abstractmethod
    def click(self, x: int, y: int) -> None:
        ...

    @abstractmethod
    def type_text(self, text: str) -> None:
        ...

    @abstractmethod
    def key(self, keyname: str) -> None:
        ...

    @abstractmethod
    def hotkey(self, modifiers: list[str], key: str) -> None:
        ...

    @abstractmethod
    def scroll(self, x: int, y: int, delta: int) -> None:
        ...
