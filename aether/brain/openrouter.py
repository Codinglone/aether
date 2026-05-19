"""OpenRouter cloud brain for fast planning and reasoning."""

from __future__ import annotations

import json
import urllib.request
from typing import Optional

from aether.core.models import UIMap, Action, ActionPlan, ActionRecord
from aether.core.brain import Brain


class OpenRouterBrain(Brain):
    """Brain that uses OpenRouter cloud API for fast reasoning.

    Recommended models:
    - openai/gpt-4o-mini    (fast, cheap, good for planning)
    - openai/gpt-4o         (best quality)
    - anthropic/claude-3-haiku (fast)
    """

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
    ):
        self.api_key = api_key
        self.model = model

    def reason(
        self,
        state: UIMap,
        task: str,
        history: list[ActionRecord],
        knowledge: Optional[str] = None,
        vision_context: Optional[str] = None,
    ) -> ActionPlan:
        """Generate an ActionPlan from current UI state and task."""
        ui_markdown = self._uimap_to_markdown(state)

        system = (
            "You are a desktop automation planner. Given a task and current UI state, produce a short action plan.\n\n"
            "AVAILABLE ACTION TYPES:\n"
            "- click(x, y): left-click at screen coordinates\n"
            "- type(text): type text string\n"
            "- key(keyname): press a key or hotkey combo (e.g. 'ctrl+l', 'Return', 'space', 'alt+Tab')\n"
            "- wait(seconds): wait for UI to load\n"
            "- scroll(x, y, delta): scroll at position (positive=down, negative=up)\n"
            "- shell(command, timeout): run a shell command to open apps\n\n"
            "CRITICAL RULES - FOLLOW EXACTLY:\n"
            "1. Check the 'app' field. If target app (Brave/YouTube/Firefox) is NOT active, use shell('brave-browser <url> &', 5) to open it.\n"
            "2. After shell opens an app, ALWAYS use wait(8) for it to fully load before any other action.\n"
            "3. After wait(8), if app is still NOT active, use key('alt+Tab') to switch to it.\n"
            "4. Before typing ANY text, you MUST first click on the target input field using coordinates from UI state.\n"
            "5. NEVER type text without clicking the input field first - text goes to whichever window is focused.\n"
            "6. To search on YouTube: click(search_box_x, search_box_y) → wait(1) → type('query') → key('Return')\n"
            "7. To play a video: click(video_thumbnail_x, video_thumbnail_y)\n"
            "8. Use exact coordinates from the UI state elements list.\n"
            "9. If the target element coordinates are not visible, use key('Tab') to navigate to it.\n\n"
            "Generate ONLY 1 action per plan. The loop will re-perceive after each action.\n"
            "Respond with a JSON ActionPlan containing exactly 1 action: {\"task_summary\": \"...\", \"actions\": [{\"type\": \"...\", \"params\": {...}, \"reason\": \"...\"}]}"
        )

        prompt = f"""Task: {task}

Current UI state (screenshot analysis):
{ui_markdown}

IMPORTANT: The 'app' field shows the currently active application. If it's NOT Brave/YouTube, you MUST open/switch to it BEFORE typing anything.

History: {len(history)} actions taken so far.

What is the SINGLE next action? Generate ONLY 1 action. The loop will re-perceive after each action, so you don't need to plan ahead. Focus on the immediate next step. Remember: shell → wait(8) → click input → type."""

        response_text = self._call_llm(prompt, system=system)
        return self._parse_action_plan(response_text)

    def explain_failure(
        self, state: UIMap, failed_action: Optional[Action], error: str
    ) -> Optional[ActionPlan]:
        """Ask the LLM for an alternative plan after a failure."""
        ui_markdown = self._uimap_to_markdown(state)

        system = (
            "The previous action failed. Suggest an alternative approach. "
            "Respond with a JSON ActionPlan only."
        )

        prompt = f"""Error: {error}

Current UI state:
{ui_markdown}

Please suggest an alternative approach."""

        response_text = self._call_llm(prompt, system=system)
        plan = self._parse_action_plan(response_text)
        if plan.actions:
            return plan
        return None

    def _call_llm(self, prompt: str, system: str, temperature: float = 0.1, max_tokens: int = 800) -> str:
        """Send prompt to OpenRouter and return response text."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        req = urllib.request.Request(
            self.BASE_URL,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://aether-native.local",
                "X-Title": "Aether-Native Agent",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"]

    def _parse_action_plan(self, response_text: str) -> ActionPlan:
        """Extract and parse JSON ActionPlan from LLM response."""
        import re

        # Try to extract JSON
        try:
            # Strip markdown fences
            lines = response_text.splitlines()
            cleaned_lines = [ln for ln in lines if not ln.strip().startswith("```")]
            cleaned = "\n".join(cleaned_lines).strip()
            data = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            # Try between ```json ... ```
            if "```json" in response_text:
                for part in response_text.split("```json")[1:]:
                    candidate = part.split("```")[0].strip()
                    try:
                        data = json.loads(candidate)
                        break
                    except json.JSONDecodeError:
                        continue
                else:
                    return ActionPlan(task_summary="", actions=[])
            else:
                return ActionPlan(task_summary="", actions=[])

        actions = []
        for action_data in data.get("actions", []):
            try:
                actions.append(
                    Action(
                        type=action_data["type"],
                        params=action_data.get("params", {}),
                        reason=action_data.get("reason", ""),
                        expected_change=action_data.get("expected_change", ""),
                    )
                )
            except (KeyError, TypeError):
                pass

        return ActionPlan(
            task_summary=data.get("task_summary", ""),
            actions=actions,
        )

    @staticmethod
    def _uimap_to_markdown(uimap: UIMap) -> str:
        """Convert UIMap to compact markdown for LLM prompt."""
        lines = [f"Screen: {uimap.screen_size[0]}x{uimap.screen_size[1]}", ""]

        def _walk(elements, depth=0):
            for elem in elements:
                indent = "  " * depth
                bounds_str = ""
                if elem.bounds:
                    bounds_str = f" (x:{elem.bounds.x}, y:{elem.bounds.y}, w:{elem.bounds.width}, h:{elem.bounds.height})"
                lines.append(f'{indent}[{elem.id}] {elem.role}: "{elem.name}"{bounds_str}')
                _walk(elem.children, depth + 1)

        _walk(uimap.elements)
        return "\n".join(lines)