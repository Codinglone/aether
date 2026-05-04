from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

from aether.core.models import UIMap, UIElement
from aether.perception.base import PerceptionAdapter


class MockPerceptionAdapter(PerceptionAdapter):
    def __init__(self, fixture_path: Path):
        with open(fixture_path) as f:
            self.fixture = json.load(f)
        self._uimap = UIMap(**self.fixture["initial_state"])
        self.state_index = 0

    def capture(self) -> UIMap:
        return self._uimap

    def get_active_window(self) -> Optional[UIElement]:
        for elem in self._uimap.elements:
            if "active" in elem.state:
                return elem
        return None

    def get_screen_size(self) -> Tuple[int, int]:
        return self._uimap.screen_size

    def find_element(self, role: Optional[str] = None, name: Optional[str] = None) -> Optional[UIElement]:
        def _search(elements: list[UIElement]) -> Optional[UIElement]:
            for elem in elements:
                match = True
                if role is not None and elem.role != role:
                    match = False
                if name is not None and elem.name != name:
                    match = False
                if match:
                    return elem
                found = _search(elem.children)
                if found:
                    return found
            return None
        return _search(self._uimap.elements)


from aether.action.base import ActionAdapter


class MockActionAdapter(ActionAdapter):
    def __init__(self):
        self.executed_actions: list[dict] = []

    def click(self, x: int, y: int) -> None:
        self.executed_actions.append({"type": "click", "x": x, "y": y})

    def type_text(self, text: str) -> None:
        self.executed_actions.append({"type": "type", "text": text})

    def hotkey(self, modifiers: list[str], key: str) -> None:
        self.executed_actions.append({"type": "hotkey", "modifiers": modifiers, "key": key})

    def scroll(self, x: int, y: int, delta: int) -> None:
        self.executed_actions.append({"type": "scroll", "x": x, "y": y, "delta": delta})

    def clear(self) -> None:
        self.executed_actions.clear()
