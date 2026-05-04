"""Local LLM integration via Ollama HTTP API - fast, private, no cloud."""

from __future__ import annotations

import json
import urllib.request
from typing import Optional


class LocalLLM:
    """Local LLM client using Ollama HTTP API.
    
    Uses small, fast models (1B-3B parameters) for speed.
    Falls back to larger models only for complex reasoning.
    """

    DEFAULT_MODEL = "llama3.2:1b"
    FAST_MODEL = "llama3.2:1b"  # 1.3GB, ~50 tokens/sec on CPU
    REASONING_MODEL = "llama3.2:1b"  # Can be upgraded to 3B/8B later

    def __init__(self, model: Optional[str] = None, base_url: str = "http://localhost:11434"):
        self.model = model or self.DEFAULT_MODEL
        self.base_url = base_url
        self._check_ollama()

    def _check_ollama(self) -> None:
        """Verify Ollama is running and model is available."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models = [m["name"] for m in data.get("models", [])]
                if self.model not in models:
                    # Try without tag
                    if f"{self.model}:latest" in models:
                        self.model = f"{self.model}:latest"
                    else:
                        raise RuntimeError(
                            f"Model '{self.model}' not found. Available: {models}. "
                            f"Run: ollama pull {self.model}"
                        )
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}: {e}. "
                "Make sure Ollama is running (ollama serve)"
            )

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        """Generate text from the local LLM.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt
            temperature: 0.0 = deterministic, 1.0 = creative
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data.get("response", "").strip()

    def analyze_screenshot(
        self,
        screenshot_path: str,
        task: str,
    ) -> dict:
        """Analyze a screenshot using the local LLM.
        
        This is the FALLBACK path - only used when AT-SPI fails.
        Returns structured data about what's on screen.
        
        Note: llama3.2:1b is text-only. For vision, we'd need a multimodal
        model like llava. This method reasons about the task without seeing
        the actual image. Vision support can be added by pulling llava:
            ollama pull llava
        
        Args:
            screenshot_path: Path to the screenshot image
            task: What the user is trying to do
            
        Returns:
            Dict with keys: found, element_name, suggested_action, coordinates, confidence
        """
        system = """You are a computer automation assistant. The user is trying to 
interact with an application but the accessibility API failed. You need to provide 
guidance on what to do next.

Respond in JSON format only:
{
    "found": true/false,
    "element_name": "name of the UI element",
    "suggested_action": "click|type|scroll|wait",
    "coordinates": {"x": 0, "y": 0},
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}"""

        prompt = f"""Task: {task}

A screenshot was captured at: {screenshot_path}

The accessibility API could not find this element. Based on the task description,
what UI element should be interacted with and where might it be located?

Respond with JSON only."""

        response = self.generate(prompt, system=system, temperature=0.0, max_tokens=300)
        
        # Try to parse JSON from response
        try:
            # Extract JSON if wrapped in markdown
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            # Return a fallback response
            return {
                "found": False,
                "element_name": "unknown",
                "suggested_action": "wait",
                "coordinates": {"x": 0, "y": 0},
                "confidence": 0.0,
                "reasoning": f"Could not parse LLM response: {response[:200]}",
            }

    def suggest_action(
        self,
        task: str,
        atspi_elements: list[dict],
        previous_actions: list[str],
    ) -> dict:
        """Suggest the next action based on current UI state.
        
        This is the BRAIN component - it reasons about what to do next.
        
        Args:
            task: The user's goal
            atspi_elements: List of accessible UI elements found
            previous_actions: History of actions taken so far
            
        Returns:
            Dict with action recommendation
        """
        system = """You are a computer automation brain. You decide what action to take next.
You have access to the OS accessibility tree (AT-SPI) which shows UI elements.

Respond in JSON only:
{
    "action": "click|type|hotkey|scroll|wait|done",
    "target": "element name or description",
    "value": "text to type if action is type",
    "reasoning": "why this action"
}"""

        elements_str = "\n".join(
            f"- {e.get('name', 'unnamed')} ({e.get('role', 'unknown')})"
            for e in atspi_elements[:20]  # Limit to avoid token overflow
        )
        
        history_str = "\n".join(f"- {a}" for a in previous_actions[-5:]) or "None"

        prompt = f"""Task: {task}

Available UI elements:
{elements_str}

Previous actions:
{history_str}

What should the next action be?"""

        response = self.generate(prompt, system=system, temperature=0.1, max_tokens=200)
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            return {
                "action": "wait",
                "target": "unknown",
                "value": "",
                "reasoning": f"Could not parse: {response[:200]}",
            }
