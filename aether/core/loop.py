from __future__ import annotations

from enum import Enum
from typing import Optional

from aether.core.models import UIMap, Action, ActionPlan, TaskResult
from aether.core.brain import Brain
from aether.core.memory import SessionMemory
from aether.core.verify import Verifier
from aether.core.safety import SafetyChecker
from aether.perception.base import PerceptionAdapter
from aether.action.base import ActionAdapter


class LoopState(Enum):
    IDLE = "idle"
    REASONING = "reasoning"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    LEARNING = "learning"
    ABORTED = "aborted"


class RalphLoop:
    def __init__(
        self,
        perception: PerceptionAdapter,
        brain: Brain,
        action: ActionAdapter,
        memory: SessionMemory,
        verifier: Verifier,
        safety: SafetyChecker,
    ):
        self.perception = perception
        self.brain = brain
        self.action = action
        self.memory = memory
        self.verifier = verifier
        self.safety = safety
        self.state = LoopState.IDLE

    def run(self, task: str) -> TaskResult:
        self.state = LoopState.REASONING
        max_retries = 3

        for attempt in range(max_retries):
            ui_map = self.perception.capture()
            plan = self.brain.reason(ui_map, task, list(self.memory.history))

            if not plan.actions:
                return TaskResult(status="failed", reason="No actions generated")

            for action in plan.actions:
                self.state = LoopState.EXECUTING

                is_safe, error = self.safety.check(action)
                if not is_safe:
                    self.state = LoopState.ABORTED
                    return TaskResult(status="aborted", reason=error)

                self._execute(action)
                from datetime import datetime, timezone
                from aether.core.models import ActionRecord
                self.memory.history.append(ActionRecord(action=action, timestamp=datetime.now(timezone.utc)))

                self.state = LoopState.VERIFYING
                new_ui_map = self.perception.capture()
                result = self.verifier.verify(ui_map, new_ui_map, action)

                if not result.success:
                    self.state = LoopState.LEARNING
                    self.memory.failed_attempts[action.type] = self.memory.failed_attempts.get(action.type, 0) + 1
                    self.brain.explain_failure(new_ui_map, action, result.details or "")
                    break

                ui_map = new_ui_map
            else:
                self.state = LoopState.IDLE
                self.memory.update_progress(task, done=True)
                return TaskResult(status="success", actions_taken=len(self.memory.history))

        return TaskResult(status="failed", reason=f"Max retries ({max_retries}) exceeded")

    def _execute(self, action: Action) -> None:
        if action.type == "click":
            self.action.click(action.params["x"], action.params["y"])
        elif action.type == "type":
            self.action.type_text(action.params["text"])
        elif action.type == "hotkey":
            self.action.hotkey(action.params.get("modifiers", []), action.params["key"])
        elif action.type == "shell":
            import subprocess
            subprocess.run(
                action.params["command"],
                shell=True,
                timeout=action.params.get("timeout", 60),
                capture_output=True,
            )
        elif action.type == "wait":
            import time
            time.sleep(action.params.get("seconds", 1))
        elif action.type == "scroll":
            self.action.scroll(
                action.params["x"], action.params["y"], action.params["delta"]
            )
