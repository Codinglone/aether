from __future__ import annotations

from typing import Optional

from aether.core.models import Action
from aether.macro.models import ElementSelector, Intent, Macro


class MacroRecorder:
    def __init__(self):
        self.current_macro: Optional[Macro] = None

    def start_recording(self, name: str) -> None:
        self.current_macro = Macro(name=name, intents=[])

    def record_action(
        self,
        action: Action,
        element_name: Optional[str] = None,
        element_role: Optional[str] = None,
    ) -> None:
        if self.current_macro is None:
            raise RuntimeError("Recording not started")
        selector = ElementSelector(role=element_role, name=element_name)
        intent = Intent(
            action_type=action.type,
            target=selector,
            params=action.params,
        )
        self.current_macro.intents.append(intent)

    def stop_recording(self) -> Optional[Macro]:
        macro = self.current_macro
        self.current_macro = None
        return macro
