from __future__ import annotations

import json
import re
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from jinja2 import Template

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


class LocalLLMBrain(Brain):
    """Brain that uses a local LLM via Ollama HTTP API for reasoning."""

    def __init__(
        self,
        model: str = "llama3.2:1b",
        base_url: str = "http://localhost:11434",
        prompt_template_path: Optional[str] = None,
    ):
        self.model = model
        self.base_url = base_url
        if prompt_template_path is None:
            prompt_template_path = str(
                Path(__file__).parent.parent / "prompts" / "planner.j2"
            )
        with open(prompt_template_path) as f:
            self._template = Template(f.read())

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

        prompt = self._template.render(
            task=task,
            ui_markdown=ui_markdown,
            history=history,
            knowledge=knowledge or "",
            vision_context=vision_context or "",
        )

        response_text = self._call_llm(prompt)
        return self._parse_action_plan(response_text)

    def explain_failure(
        self, state: UIMap, failed_action: Optional[Action], error: str
    ) -> Optional[ActionPlan]:
        """Ask the LLM for an alternative plan after a failure."""
        ui_markdown = self._uimap_to_markdown(state)

        failure_prompt = f"""The previous action failed.

Error: {error}

Current UI state:
{ui_markdown}

Please suggest an alternative approach.

Respond with a JSON ActionPlan only."""

        response_text = self._call_llm(failure_prompt)
        plan = self._parse_action_plan(response_text)
        if plan.actions:
            return plan
        return None

    def _call_llm(self, prompt: str, temperature: float = 0.1, max_tokens: int = 800) -> str:
        """Send a prompt to the local LLM and return the response text."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data.get("response", "").strip()

    def _parse_action_plan(self, response_text: str) -> ActionPlan:
        """Extract and parse JSON ActionPlan from LLM response."""
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if not json_match:
            json_match = re.search(r"```\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if not json_match:
            # Try to find raw JSON object
            json_match = re.search(r"(\{.*\})", response_text, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text

        try:
            data = json.loads(json_str)
            actions = []
            for action_data in data.get("actions", []):
                actions.append(
                    Action(
                        type=action_data["type"],
                        params=action_data.get("params", {}),
                        reason=action_data.get("reason", ""),
                        expected_change=action_data.get("expected_change", ""),
                    )
                )
            return ActionPlan(
                task_summary=data.get("task_summary", ""),
                actions=actions,
            )
        except (json.JSONDecodeError, KeyError):
            # Return empty plan on parse failure
            return ActionPlan(task_summary="", actions=[])

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
