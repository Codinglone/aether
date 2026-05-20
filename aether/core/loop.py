from __future__ import annotations

from enum import Enum
from typing import Optional

from aether.core.models import UIMap, Action, ActionPlan, TaskResult
from aether.core.brain import Brain
from aether.core.memory import SessionMemory
from aether.core.verify import Verifier
from aether.core.safety import SafetyChecker
from aether.core.knowledge import KnowledgeStore
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
        knowledge: Optional[KnowledgeStore] = None,
    ):
        self.perception = perception
        self.brain = brain
        self.action = action
        self.memory = memory
        self.verifier = verifier
        self.safety = safety
        self.knowledge = knowledge
        self.state = LoopState.IDLE
        self.max_retries = 3

    def run(self, task: str) -> TaskResult:
        self.state = LoopState.REASONING

        # Load relevant knowledge for this task
        knowledge_text = ""
        if self.knowledge:
            app_hint = self._infer_app_from_task(task)
            if app_hint:
                knowledge_text = self.knowledge.render_for_prompt(app_hint, task)

        for attempt in range(self.max_retries):
            print(f"\n--- Loop iteration {attempt + 1}/{self.max_retries} ---")
            
            # 1. PERCEIVE
            print("  [1] Perceiving...")
            ui_map = self.perception.capture()
            app_name = ui_map.active_window.name if ui_map.active_window else "unknown"
            print(f"  [1] Active app: {app_name}, Elements: {len(ui_map.elements)}")

            # 2. REASON
            print("  [2] Planning...")
            plan = self.brain.reason(
                state=ui_map,
                task=task,
                history=list(self.memory.history),
                knowledge=knowledge_text or None,
            )

            if not plan.actions:
                print("  [2] No actions generated")
                return TaskResult(status="failed", reason="No actions generated")
            
            print(f"  [2] Planned {len(plan.actions)} actions: {[(a.type, a.reason[:40]) for a in plan.actions]}")

            # Execute ONLY the first action from the plan, then re-perceive and re-plan
            action = plan.actions[0]
            self.state = LoopState.EXECUTING

            # Enforce: before typing, must be in target app
            action = self._enforce_app_focus(action, task, ui_map)

            # 3. SAFETY
            is_safe, error = self.safety.check(action)
            if not is_safe:
                self.state = LoopState.ABORTED
                return TaskResult(status="aborted", reason=error)

            # 4. EXECUTE
            print(f"  [4] Executing: {action.type}({action.params}) — {action.reason[:50]}")
            self._execute(action)
            self.memory.record_action(action)

            # 5. VERIFY
            self.state = LoopState.VERIFYING
            print("  [5] Verifying...")
            new_ui_map = self.perception.capture()
            result = self.verifier.verify(ui_map, new_ui_map, action)
            print(f"  [5] Verify result: success={result.success}, strategy={result.matched_strategy}, details={result.details[:60] if result.details else ''}")

            if not result.success:
                # 6. LEARN
                self.state = LoopState.LEARNING
                self.memory.record_failure(action, result.details or "Verification failed")
                print("  [6] Verification failed, retrying...")
                # The outer loop will retry with a fresh plan
                continue

            # Check if task is complete (e.g. audio playing for video tasks)
            is_complete = self._is_task_complete(task, new_ui_map)
            print(f"  [7] Task complete check: {is_complete}")
            if is_complete:
                self.state = LoopState.IDLE
                self.memory.mark_task_done(task)
                print("  [7] Task complete! Returning success.")
                return TaskResult(status="success", actions_taken=len(self.memory.history))

        return TaskResult(status="failed", reason=f"Max retries ({self.max_retries}) exceeded")

    def _enforce_app_focus(self, action: Action, task: str, ui_map: UIMap) -> Action:
        """Before typing, ensure the target app is active using xdotool."""
        if action.type not in ("type", "click"):
            return action

        # Guess target app from task
        task_lower = task.lower()
        target_app = None
        if "brave" in task_lower:
            target_app = "brave"
        elif "firefox" in task_lower:
            target_app = "firefox"
        elif "chrome" in task_lower:
            target_app = "chrome"
        elif "spotify" in task_lower:
            target_app = "spotify"

        if not target_app:
            return action

        # Check current window title using xdotool
        current_title = ""
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0:
                current_title = result.stdout.strip().lower()
        except Exception:
            pass

        if target_app in current_title:
            return action  # Already focused

        # Try to focus target app with xdotool
        print(f"  [Focus] Current window: '{current_title[:40]}', need: {target_app}. Focusing...")
        try:
            subprocess.run(
                ["xdotool", "search", "--name", target_app, "windowactivate"],
                capture_output=True, timeout=3,
            )
            time.sleep(0.5)
        except Exception:
            pass

        # If still not focused and it's a type action, return focus action
        if action.type == "type":
            return Action(
                type="shell",
                params={"command": f"xdotool search --name {target_app} windowactivate", "timeout": 2},
                reason=f"Focus {target_app} window before typing",
                expected_change=f"{target_app} window becomes active",
            )

        return action

    def _is_task_complete(self, task: str, ui_map: UIMap) -> bool:
        """Check if the task appears complete based on current state."""
        task_lower = task.lower()

        # For video/music tasks
        if any(kw in task_lower for kw in ["play", "video", "music", "song", "youtube"]):
            # Check 1: Is Brave running with YouTube?
            if not self._is_app_running("brave"):
                return False

            # Check 2: Is audio playing?
            if not self._check_audio_playing():
                return False

            # Check 3: Is the active window a browser?
            try:
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True, text=True, timeout=2,
                )
                if result.returncode == 0:
                    title = result.stdout.lower()
                    if "youtube" in title or "brave" in title:
                        return True
            except Exception:
                pass

            return False

        return False

    @staticmethod
    def _is_app_running(app_name: str) -> bool:
        """Check if an app process is running."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", app_name],
                capture_output=True, timeout=2,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def _check_audio_playing() -> bool:
        """Check if any audio stream is active."""
        try:
            result = subprocess.run(
                ["pactl", "list", "sink-inputs"],
                capture_output=True, text=True, timeout=2,
            )
            return result.returncode == 0 and "Sink Input" in result.stdout
        except Exception:
            return False

    def _execute(self, action: Action) -> None:
        if action.type == "click":
            self.action.click(action.params["x"], action.params["y"])
        elif action.type == "type":
            self.action.type_text(action.params["text"])
        elif action.type == "key":
            self.action.key(action.params.get("key", action.params.get("keys", "Return")))
        elif action.type == "hotkey":
            self.action.hotkey(action.params.get("modifiers", []), action.params["key"])
        elif action.type == "shell":
            import subprocess
            # Use Popen for non-blocking shell commands (e.g. opening browser)
            subprocess.Popen(
                action.params["command"],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait briefly for app to launch
            import time
            time.sleep(action.params.get("timeout", 3))
        elif action.type == "wait":
            import time
            time.sleep(action.params.get("seconds", 1))
        elif action.type == "scroll":
            self.action.scroll(
                action.params["x"], action.params["y"], action.params["delta"]
            )

    @staticmethod
    def _infer_app_from_task(task: str) -> Optional[str]:
        """Naive heuristic to guess the target app from task text."""
        task_lower = task.lower()
        app_keywords = {
            "brave": "Brave",
            "firefox": "Firefox",
            "chrome": "Chrome",
            "settings": "GNOME Settings",
            "calculator": "Calculator",
            "terminal": "Terminal",
            "discord": "Discord",
            "cursor": "Cursor",
        }
        for keyword, app_name in app_keywords.items():
            if keyword in task_lower:
                return app_name
        return None
