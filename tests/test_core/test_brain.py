import json
import urllib.request
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from aether.core.models import UIMap, UIElement, Bounds, ActionPlan
from aether.core.brain import LocalLLMBrain


class TestLocalLLMBrain:
    def _make_uimap(self) -> UIMap:
        return UIMap(
            screen_size=(1920, 1080),
            elements=[
                UIElement(
                    id="btn_save",
                    role="push button",
                    name="Save",
                    bounds=Bounds(x=100, y=100, width=50, height=30),
                    state=set(),
                )
            ],
        )

    def _mock_ollama_response(self, response_text: str):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"response": response_text}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    def test_reason_returns_actionplan(self):
        brain = LocalLLMBrain(model="llama3.2:1b")
        uimap = self._make_uimap()

        json_response = json.dumps({
            "task_summary": "Click Save",
            "actions": [
                {
                    "type": "click",
                    "params": {"x": 125, "y": 115},
                    "reason": "Click the Save button",
                    "expected_change": "Save dialog opens",
                }
            ]
        })

        mock_resp = self._mock_ollama_response(json_response)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            plan = brain.reason(uimap, "Click Save", [])

        assert isinstance(plan, ActionPlan)
        assert plan.task_summary == "Click Save"
        assert len(plan.actions) == 1
        assert plan.actions[0].type == "click"
        assert plan.actions[0].params["x"] == 125

    def test_reason_parses_json_from_markdown(self):
        brain = LocalLLMBrain(model="llama3.2:1b")
        uimap = self._make_uimap()

        markdown_response = """Here is the plan:
```json
{
  "task_summary": "Click Save",
  "actions": [
    {
      "type": "click",
      "params": {"x": 125, "y": 115},
      "reason": "Click the Save button",
      "expected_change": "Save dialog opens"
    }
  ]
}
```"""

        mock_resp = self._mock_ollama_response(markdown_response)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            plan = brain.reason(uimap, "Click Save", [])

        assert isinstance(plan, ActionPlan)
        assert len(plan.actions) == 1

    def test_reason_returns_empty_plan_on_invalid_json(self):
        brain = LocalLLMBrain(model="llama3.2:1b")
        uimap = self._make_uimap()

        mock_resp = self._mock_ollama_response("not json at all")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            plan = brain.reason(uimap, "Click Save", [])

        assert isinstance(plan, ActionPlan)
        assert len(plan.actions) == 0

    def test_explain_failure_returns_alternative_plan(self):
        brain = LocalLLMBrain(model="llama3.2:1b")
        uimap = self._make_uimap()

        json_response = json.dumps({
            "task_summary": "Retry with keyboard shortcut",
            "actions": [
                {
                    "type": "hotkey",
                    "params": {"modifiers": ["ctrl"], "key": "s"},
                    "reason": "Use keyboard shortcut instead",
                    "expected_change": "Save dialog opens",
                }
            ]
        })

        mock_resp = self._mock_ollama_response(json_response)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            plan = brain.explain_failure(uimap, None, "Click did not work")

        assert isinstance(plan, ActionPlan)
        assert plan.actions[0].type == "hotkey"

    def test_explain_failure_returns_none_on_invalid_json(self):
        brain = LocalLLMBrain(model="llama3.2:1b")
        uimap = self._make_uimap()

        mock_resp = self._mock_ollama_response("garbage")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            plan = brain.explain_failure(uimap, None, "error")

        assert plan is None
