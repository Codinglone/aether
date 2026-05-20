#!/usr/bin/env python3
"""
Aether HYBRID AGENT Demo

Combines:
- OpenRouter vision (fast, multimodal) 
- Local Ollama planning (llama3.2:1b, free, fast on CPU)
- Silent screenshot capture with GNOME sound suppression
- xdotool window focus enforcement
- Better task completion detection

Task: Play International Love by Chris Brown on YouTube.
"""

import json
import subprocess
import sys
import time
import urllib.request

from aether.perception.vision_first import VisionFirstPerceptionAdapter
from aether.action.ydotool import YdotoolActionAdapter
from aether.core.memory import SessionMemory
from aether.core.desktop_verify import DesktopVerifier
from aether.core.safety import DummySafetyChecker
from aether.core.loop import RalphLoop
from aether.core.models import UIMap, ActionPlan, ActionRecord


class LocalOllamaBrain:
    """Local planning brain using Ollama HTTP API."""

    def __init__(self, model: str = "llama3.2:1b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def reason(self, state: UIMap, task: str, history: list, knowledge=None, vision_context=None):
        # Convert UI state to compact text
        ui_text = f"Screen: {state.screen_size[0]}x{state.screen_size[1]}\n"
        ui_text += f"App: {state.active_window.name if state.active_window else 'unknown'}\n"
        for elem in state.elements[:15]:
            if elem.bounds:
                ui_text += f"  - {elem.name} ({elem.role}) at ({elem.bounds.x}, {elem.bounds.y})\n"
            else:
                ui_text += f"  - {elem.name} ({elem.role})\n"

        system = (
            "You are a desktop automation planner. Generate exactly 1 action.\n"
            "Action types: click(x,y), type(text), key(keyname), wait(seconds), shell(command)\n"
            "CRITICAL: Click input fields BEFORE typing. Use shell to open apps.\n"
            "Return JSON: {\"actions\":[{\"type\":\"...\",\"params\":{...},\"reason\":\"...\"}]}"
        )

        prompt = f"Task: {task}\n\nUI State:\n{ui_text}\n\nHistory: {len(history)} actions\n\nNext action?"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 300},
        }

        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            response = data.get("response", "").strip()

        return self._parse_action_plan(response)

    def explain_failure(self, state, failed_action, error):
        # Simple retry with same logic
        return None

    @staticmethod
    def _parse_action_plan(response_text: str) -> ActionPlan:
        import re
        try:
            # Extract JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                match = re.search(r"\{.*\}", response_text, re.DOTALL)
                json_str = match.group(0) if match else response_text

            data = json.loads(json_str)
            actions = []
            for action_data in data.get("actions", []):
                actions.append(Action(
                    type=action_data["type"],
                    params=action_data.get("params", {}),
                    reason=action_data.get("reason", ""),
                    expected_change="",
                ))
            return ActionPlan(task_summary="", actions=actions)
        except Exception:
            return ActionPlan(task_summary="", actions=[])


class FocusManager:
    """Manages window focus using xdotool/wmctrl."""

    @staticmethod
    def focus_app(app_name: str) -> bool:
        """Focus a window by app name using xdotool."""
        try:
            # Search for window and activate it
            result = subprocess.run(
                ["xdotool", "search", "--name", app_name, "windowactivate"],
                capture_output=True, timeout=5,
            )
            if result.returncode == 0:
                time.sleep(0.5)
                return True

            # Try wmctrl
            result = subprocess.run(
                ["wmctrl", "-a", app_name],
                capture_output=True, timeout=5,
            )
            if result.returncode == 0:
                time.sleep(0.5)
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def get_active_window_title() -> str:
        """Get the currently focused window title."""
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""


class SoundSuppressor:
    """Temporarily suppresses GNOME notification sounds."""

    def __init__(self):
        self._original_setting = None

    def __enter__(self):
        """Suppress sounds on enter."""
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.sound", "event-sounds"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0:
                self._original_setting = result.stdout.strip()
                subprocess.run(
                    ["gsettings", "set", "org.gnome.desktop.sound", "event-sounds", "false"],
                    capture_output=True, timeout=2,
                )
        except Exception:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore sounds on exit."""
        if self._original_setting is not None:
            try:
                subprocess.run(
                    ["gsettings", "set", "org.gnome.desktop.sound", "event-sounds", self._original_setting],
                    capture_output=True, timeout=2,
                )
            except Exception:
                pass


class EnhancedDesktopVerifier(DesktopVerifier):
    """Enhanced verifier with better task completion detection."""

    def verify(self, before, after, action):
        # Call parent verifier
        result = super().verify(before, after, action)
        return result

    @staticmethod
    def is_youtube_playing() -> bool:
        """Check if a YouTube video is currently playing."""
        try:
            # Check if Brave is running with YouTube
            result = subprocess.run(
                ["pgrep", "-a", "brave"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                if "youtube.com/watch" in output or "youtube.com" in output:
                    # Check for audio
                    audio = subprocess.run(
                        ["pactl", "list", "sink-inputs"],
                        capture_output=True, text=True, timeout=2,
                    )
                    if audio.returncode == 0 and "Sink Input" in audio.stdout:
                        return True
        except Exception:
            pass
        return False

    @staticmethod
    def is_app_focused(app_name: str) -> bool:
        """Check if app is the focused window."""
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0:
                return app_name.lower() in result.stdout.lower()
        except Exception:
            pass
        return False


def main():
    api_key = "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"

    print("=" * 70)
    print("AETHER HYBRID AGENT")
    print("Vision: OpenRouter (cloud) | Planning: Ollama llama3.2:1b (local)")
    print("Focus: xdotool | Sound: suppressed | Completion: enhanced")
    print("=" * 70)

    # 1. Perception — OpenRouter cloud vision
    perception = VisionFirstPerceptionAdapter(
        openrouter_api_key=api_key,
        openrouter_model="openai/gpt-4o-mini",
        vision_timeout=45.0,
        screenshot_scale=320,
    )

    # 2. Brain — LOCAL Ollama planning (free!)
    brain = LocalOllamaBrain(model="llama3.2:1b")

    # 3. Actions — Wayland-native via ydotool
    action = YdotoolActionAdapter(socket_path="/tmp/.ydotool_socket")

    # 4. Memory, verifier, safety
    memory = SessionMemory()
    verifier = EnhancedDesktopVerifier()
    safety = DummySafetyChecker()

    # 5. Assemble loop
    loop = RalphLoop(
        perception=perception,
        brain=brain,
        action=action,
        memory=memory,
        verifier=verifier,
        safety=safety,
    )

    # 6. Run task with sound suppression
    task = (
        "Open Brave browser, go to YouTube, search for 'International love chris brown', "
        "and play the first video."
    )
    if len(sys.argv) > 1:
        task = sys.argv[1]

    print(f"\nTask: {task}\n")

    with SoundSuppressor():
        start = time.time()
        try:
            result = loop.run(task)
            elapsed = time.time() - start
            print(f"\n{'='*70}")
            print(f"Result: {result.status}")
            print(f"Actions taken: {result.actions_taken}")
            if result.reason:
                print(f"Reason: {result.reason}")
            print(f"Elapsed: {elapsed:.1f}s")
            print(f"Vision stats: {perception.get_stats()}")
            print(f"{'='*70}")
        except KeyboardInterrupt:
            print("\n[Agent] Interrupted by user.")
        except Exception as e:
            print(f"\n[Agent] Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()