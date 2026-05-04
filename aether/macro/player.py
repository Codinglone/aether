from __future__ import annotations

from aether.macro.models import Macro, Intent
from aether.perception.base import PerceptionAdapter
from aether.action.base import ActionAdapter


class MacroPlayer:
    def __init__(self, perception: PerceptionAdapter, action: ActionAdapter):
        self.perception = perception
        self.action = action

    def play(self, macro: Macro) -> None:
        for intent in macro.intents:
            self._execute_intent(intent)

    def _execute_intent(self, intent: Intent) -> None:
        element = self.perception.find_element(
            role=intent.target.role,
            name=intent.target.name,
        )
        if element is None:
            # Self-healing: fuzzy match by role only
            element = self.perception.find_element(role=intent.target.role)

        if element is None:
            raise RuntimeError(
                f"Could not resolve element for intent: {intent.target}"
            )

        if intent.action_type == "click":
            center_x = element.bounds.x + element.bounds.width // 2
            center_y = element.bounds.y + element.bounds.height // 2
            self.action.click(center_x, center_y)
        elif intent.action_type == "type":
            text = intent.params.get("text", "")
            self.action.type_text(text)
        elif intent.action_type == "hotkey":
            mods = intent.params.get("modifiers", [])
            key = intent.params.get("key", "")
            self.action.hotkey(mods, key)
