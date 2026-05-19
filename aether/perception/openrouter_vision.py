"""OpenRouter cloud vision client for fast screenshot analysis."""

from __future__ import annotations

import base64
import json
import urllib.request
from typing import Optional


class OpenRouterVisionClient:
    """Client for OpenRouter API with vision support.

    Uses cloud multimodal models for fast screenshot analysis.
    Recommended models:
    - google/gemini-flash-1.5  (fastest, cheapest)
    - openai/gpt-4o-mini       (fast, good)
    - openai/gpt-4o            (best quality)
    - anthropic/claude-3-haiku (fast)
    """

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "google/gemini-flash-1.5"):
        self.api_key = api_key
        self.model = model

    def analyze_screenshot(self, image_path: str, prompt: str) -> str:
        """Analyze a screenshot and return text description."""
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        # Detect image format from extension
        ext = image_path.split(".")[-1].lower()
        if ext == "jpg" or ext == "jpeg":
            mime = "image/jpeg"
        elif ext == "png":
            mime = "image/png"
        else:
            mime = "image/png"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{img_b64}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1,
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

    def analyze_screenshot_structured(
        self, image_path: str, screen_size: tuple[int, int]
    ) -> dict:
        """Analyze screenshot and return structured UI elements.

        Returns dict with:
        - description: str
        - app: str
        - elements: list of {name, type, x, y, confidence}
        """
        prompt = f"""You are a desktop automation assistant analyzing a screenshot.

Screen resolution: {screen_size[0]}x{screen_size[1]} pixels.

Describe the screen state and list visible interactive UI elements with their approximate center coordinates.

Return ONLY a JSON object with this exact structure. No markdown fences, no explanations, just raw JSON:
{{"description": "brief description", "app": "foreground application name", "elements": [{{"name": "element label", "type": "button|input|link|text|menu", "x": 500, "y": 300, "confidence": 0.9}}]}}"""

        response = self.analyze_screenshot(image_path, prompt)

        # Robust JSON extraction from markdown-fenced responses
        import re

        def _try_parse(text: str):
            """Try to parse JSON, return dict or None."""
            text = text.strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None

        # Strategy 1: Strip markdown fence lines, parse remainder
        lines = response.splitlines()
        cleaned_lines = [ln for ln in lines if not ln.strip().startswith("```")]
        cleaned = "\n".join(cleaned_lines).strip()
        parsed = _try_parse(cleaned)
        if parsed:
            return parsed

        # Strategy 2: Find content between ```json ... ```
        if "```json" in response:
            for part in response.split("```json")[1:]:
                candidate = part.split("```")[0].strip()
                parsed = _try_parse(candidate)
                if parsed:
                    return parsed

        # Strategy 3: Find content between any ``` ... ```
        if "```" in response:
            for part in response.split("```")[1:]:
                candidate = part.strip()
                parsed = _try_parse(candidate)
                if parsed:
                    return parsed

        # Strategy 4: Find first { ... } block
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            parsed = _try_parse(match.group(0))
            if parsed:
                return parsed

        # Fallback: return raw text
        return {
            "description": response[:500],
            "app": "unknown",
            "elements": [],
            "raw_response": response,
        }