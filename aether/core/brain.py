from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from aether.core.models import UIMap, Action, ActionPlan, ActionRecord


class Brain(ABC):
    @abstractmethod
    def reason(self, state: UIMap, task: str, history: list[ActionRecord]) -> ActionPlan:
        ...

    @abstractmethod
    def explain_failure(
        self, state: UIMap, failed_action: Optional[Action], error: str
    ) -> Optional[ActionPlan]:
        ...


class StubBrain(Brain):
    """Stub brain that returns hardcoded actions for testing."""

    def reason(self, state: UIMap, task: str, history: list[ActionRecord]) -> ActionPlan:
        def find_button(elements):
            for elem in elements:
                if elem.role == "push button":
                    return elem
                found = find_button(elem.children)
                if found:
                    return found
            return None

        target = find_button(state.elements)

        if target:
            center_x = target.bounds.x + target.bounds.width // 2
            center_y = target.bounds.y + target.bounds.height // 2
            return ActionPlan(
                task_summary=task,
                actions=[
                    Action(
                        type="click",
                        params={"x": center_x, "y": center_y},
                        reason=f"Click {target.name}",
                        expected_change="State changes",
                    )
                ],
            )
        return ActionPlan(task_summary=task, actions=[])

    def explain_failure(
        self, state: UIMap, failed_action: Optional[Action], error: str
    ) -> Optional[ActionPlan]:
        return None
