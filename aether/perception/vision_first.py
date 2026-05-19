"""Vision-first perception: screenshot + llava primary, AT-SPI fallback."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Optional, Tuple

import pyatspi

from aether.perception.base import PerceptionAdapter
from aether.core.models import UIMap, UIElement, Bounds


class VisionFirstPerceptionAdapter(PerceptionAdapter):
    """Vision-first perception adapter.

    PRIMARY path (vision):
    1. Capture screenshot
    2. Send to vision model (OpenRouter cloud OR local llava via Ollama)
    3. Parse structured UI description from response

    FALLBACK path (AT-SPI, fast):
    1. Query AT-SPI accessibility tree
    2. Get element names, roles, coordinates
    3. Use when vision times out or fails

    Configuration:
    - vision_timeout: seconds to wait for vision (default 30 for cloud, 120 for local)
    - screenshot_scale: max width for screenshots (default 640 for speed)
    - openrouter_api_key: if set, uses OpenRouter cloud vision (fast)
    - openrouter_model: OpenRouter model name (default google/gemini-2.5-flash)
    """

    def __init__(
        self,
        vision_model: str = "llava:7b",
        vision_timeout: float = 120.0,
        screenshot_scale: int = 640,
        ollama_url: str = "http://localhost:11434",
        openrouter_api_key: Optional[str] = None,
        openrouter_model: str = "google/gemini-2.5-flash",
    ):
        self.vision_model = vision_model
        self.vision_timeout = vision_timeout
        self.screenshot_scale = screenshot_scale
        self.ollama_url = ollama_url
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_model = openrouter_model
        self._use_cloud = openrouter_api_key is not None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._vision_count = 0
        self._fallback_count = 0
        self._screen_size = self._get_screen_size()
        self._last_screenshot_size = (640, 360)  # default, updated after capture

    def capture(self) -> UIMap:
        """Capture UI state. Try vision first, fall back to AT-SPI."""
        # Try vision first
        vision_future = self._executor.submit(self._capture_with_vision)
        try:
            result = vision_future.result(timeout=self.vision_timeout)
            if result and result.elements:
                self._vision_count += 1
                return result
        except FutureTimeoutError:
            print(f"  [Perception] Vision timed out after {self.vision_timeout}s, using AT-SPI fallback")
        except Exception as e:
            print(f"  [Perception] Vision failed: {e}, using AT-SPI fallback")
            import traceback, os
            # Check if screenshot exists and its size
            try:
                ss_files = sorted([f for f in os.listdir('/tmp') if f.startswith('aether_vision_') and f.endswith('.png')], key=lambda x: os.path.getmtime(os.path.join('/tmp', x)), reverse=True)
                if ss_files:
                    latest = os.path.join('/tmp', ss_files[0])
                    print(f"    Latest screenshot: {latest} ({os.path.getsize(latest)} bytes)")
            except Exception:
                pass

        # Fallback to AT-SPI
        self._fallback_count += 1
        return self._capture_with_atspi()

    def _capture_with_vision(self) -> UIMap:
        """Capture screenshot and analyze with vision model (cloud or local)."""
        screenshot_path = self._capture_screenshot()
        # Track actual screenshot dimensions for coordinate scaling
        try:
            from PIL import Image
            with Image.open(screenshot_path) as img:
                self._last_screenshot_size = img.size
        except Exception:
            pass
        if self._use_cloud:
            analysis = self._analyze_with_openrouter(screenshot_path)
        else:
            analysis = self._analyze_with_llava(screenshot_path)
        return self._parse_vision_result(analysis)

    def _capture_screenshot(self) -> str:
        """Capture screenshot via GNOME portal (Wayland) or ffmpeg fallback (X11)."""
        # Try GNOME portal first (works on Wayland)
        portal_path = self._capture_via_portal()
        if portal_path:
            # Resize to smaller PNG for smaller base64
            if self.screenshot_scale > 0:
                resized = f"/tmp/aether_vision_{int(time.time())}.png"
                result = subprocess.run(
                    ["ffmpeg", "-y", "-i", portal_path, "-vf",
                     f"scale={self.screenshot_scale}:-1",
                     "-vframes", "1", "-update", "1", resized],
                    capture_output=True, timeout=10,
                )
                if result.returncode == 0:
                    return resized
            return portal_path

        # Fallback to ffmpeg x11grab
        path = f"/tmp/aether_vision_{int(time.time())}.png"
        scale_filter = f"scale={self.screenshot_scale}:-1"
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "x11grab", "-i", ":0",
             "-vframes", "1", "-vf", scale_filter, path],
            capture_output=True, timeout=10,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Screenshot failed: {result.stderr.decode()[-200:]}")
        return path

    def _capture_via_portal(self) -> Optional[str]:
        """Use freedesktop portal to capture screenshot on Wayland."""
        import glob
        pictures_dir = os.path.expanduser("~/Pictures")
        # Remove old screenshots
        for f in glob.glob(os.path.join(pictures_dir, "Screenshot*.png")):
            try:
                os.remove(f)
            except OSError:
                pass

        # Call portal
        result = subprocess.run(
            ["gdbus", "call", "--session",
             "--dest", "org.freedesktop.portal.Desktop",
             "--object-path", "/org/freedesktop/portal/desktop",
             "--method", "org.freedesktop.portal.Screenshot.Screenshot",
             "", "{}"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None

        # Poll for screenshot file
        for _ in range(20):
            time.sleep(0.3)
            files = glob.glob(os.path.join(pictures_dir, "Screenshot*.png"))
            if files:
                return files[0]
        return None

    def _analyze_with_llava(self, image_path: str) -> str:
        """Send screenshot to llava via Ollama."""
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        prompt = (
            "Describe this screenshot for a desktop automation agent. "
            "List visible UI elements with approximate pixel coordinates. "
            "Format: element_name (type) at (x, y). "
            "Screen is {}x{} pixels."
        ).format(self._screen_size[0], self._screen_size[1])

        payload = {
            "model": self.vision_model,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 400},
        }

        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
            return data.get("response", "").strip()

    def _analyze_with_openrouter(self, image_path: str) -> str:
        """Send screenshot to OpenRouter cloud vision API with retries."""
        import urllib.error

        # Verify file exists and has content
        if not os.path.exists(image_path) or os.path.getsize(image_path) < 100:
            raise RuntimeError(f"Invalid screenshot: {image_path} ({os.path.getsize(image_path) if os.path.exists(image_path) else 'missing'} bytes)")

        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        # Detect mime type from extension
        ext = image_path.split(".")[-1].lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"

        sw, sh = self._last_screenshot_size
        dw, dh = self._screen_size
        prompt = (
            f"You are a desktop automation assistant analyzing a {dw}x{dh} display. "
            f"This is a resized screenshot ({sw}x{sh}). "
            f"Coordinates MUST be in the original {dw}x{dh} display space (e.g. x ranges 0-{dw}, y ranges 0-{dh}).\n\n"
            "List the foreground application name in 'app' (e.g. 'Brave', 'Firefox', 'VS Code', 'Terminal', 'YouTube'). "
            "List up to 10 interactive UI elements with their center coordinates in the original display space. "
            "Return ONLY JSON: {\"description\": \"...\", \"app\": \"...\", \"elements\": [{\"name\": \"...\", \"type\": \"...\", \"x\": 1234, \"y\": 567, \"confidence\": 0.9}]}. "
            "No markdown fences."
        )

        payload = {
            "model": self.openrouter_model,
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
            "max_tokens": 800,
            "temperature": 0.1,
        }

        last_error = None
        for attempt in range(3):
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "HTTP-Referer": "https://aether-native.local",
                    "X-Title": "Aether-Native Agent",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode())
                    return data["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                last_error = e
                error_body = e.read().decode()[:200]
                print(f"    [Vision] HTTP {e.code} on attempt {attempt + 1}: {error_body}")
                if e.code == 429:  # Rate limit
                    time.sleep(2 ** attempt)
                elif e.code == 400:
                    # Try with smaller image on next attempt
                    if attempt == 0 and os.path.getsize(image_path) > 50000:
                        print(f"    [Vision] Retrying with smaller screenshot...")
                        # Resize more aggressively
                        smaller = f"/tmp/aether_vision_small_{int(time.time())}.png"
                        result = subprocess.run(
                            ["ffmpeg", "-y", "-i", image_path, "-vf", "scale=160:-1",
                             "-vframes", "1", "-update", "1", smaller],
                            capture_output=True, timeout=10,
                        )
                        if result.returncode == 0:
                            image_path = smaller
                            with open(image_path, "rb") as f:
                                img_b64 = base64.b64encode(f.read()).decode()
                            # Update payload with new image
                            payload["messages"][0]["content"][1]["image_url"]["url"] = f"data:{mime};base64,{img_b64}"
                        time.sleep(1)
                    else:
                        time.sleep(1)
                else:
                    time.sleep(1)
            except Exception as e:
                last_error = e
                print(f"    [Vision] Error on attempt {attempt + 1}: {e}")
                time.sleep(1)

        raise last_error if last_error else RuntimeError("All vision attempts failed")

    def _scale_coords(self, x: int, y: int) -> tuple[int, int]:
        """Scale coordinates from screenshot space to actual display space."""
        sw, sh = self._last_screenshot_size
        dw, dh = self._screen_size
        scale_x = dw / max(sw, 1)
        scale_y = dh / max(sh, 1)
        return int(x * scale_x), int(y * scale_y)

    def _parse_vision_result(self, text: str) -> UIMap:
        """Parse vision response into UIMap.

        Handles both structured JSON (OpenRouter) and text patterns (llava).
        Coordinates are scaled from screenshot space to actual display space.
        """
        import re

        # Try structured JSON first
        parsed = self._try_parse_json(text)
        if parsed and "elements" in parsed:
            elements = []
            for elem_data in parsed.get("elements", []):
                raw_x = elem_data.get("x", 0)
                raw_y = elem_data.get("y", 0)
                scaled_x, scaled_y = self._scale_coords(raw_x, raw_y)
                elements.append(UIElement(
                    id=f"vision_{len(elements)}",
                    name=elem_data.get("name", "")[:100],
                    role=elem_data.get("type", "unknown"),
                    bounds=Bounds(
                        x=scaled_x,
                        y=scaled_y,
                        width=50,
                        height=50,
                    ),
                    metadata={
                        "source": "openrouter_vision" if self._use_cloud else "llava_vision",
                        "confidence": elem_data.get("confidence", 0.5),
                        "raw_coords": f"({raw_x}, {raw_y})",
                    },
                ))
            # Extract app name for active_window
            app_name = parsed.get("app", "unknown")
            active_window = UIElement(
                id=f"active_{app_name}",
                name=app_name,
                role="application",
                app=app_name,
            ) if app_name and app_name != "unknown" else None
        return UIMap(
            screen_size=self._screen_size,
            elements=elements,
            active_window=None,
        )

        # Fallback: parse text patterns (llava format)
        elements = []
        for line in text.split("\n"):
            coords = re.findall(r"(\d{2,4})\s*[;,]\s*(\d{2,4})", line)
            if coords:
                x, y = int(coords[0][0]), int(coords[0][1])
                name = line.strip()
                role = "unknown"
                if "button" in line.lower():
                    role = "button"
                elif "input" in line.lower() or "text" in line.lower():
                    role = "text"
                elif "link" in line.lower():
                    role = "link"
                elif "menu" in line.lower():
                    role = "menu"

                elements.append(UIElement(
                    id=f"vision_{len(elements)}",
                    name=name[:100],
                    role=role,
                    bounds=Bounds(x=x, y=y, width=50, height=50),
                    metadata={"source": "llava_vision", "raw": line},
                ))

        return UIMap(
            screen_size=self._screen_size,
            elements=elements,
        )

    @staticmethod
    def _try_parse_json(text: str) -> Optional[dict]:
        """Try to extract JSON from text, handling markdown fences."""
        text = text.strip()
        import re

        # Strip markdown fence lines
        lines = text.splitlines()
        cleaned_lines = [ln for ln in lines if not ln.strip().startswith("```")]
        cleaned = "\n".join(cleaned_lines).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try between ```json ... ```
        if "```json" in text:
            for part in text.split("```json")[1:]:
                candidate = part.split("```")[0].strip()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        # Try between any ``` ... ```
        if "```" in text:
            for part in text.split("```")[1:]:
                candidate = part.strip()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        # Try raw { ... }
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _capture_with_atspi(self) -> UIMap:
        """Capture UI state via AT-SPI (fallback)."""
        desktop = pyatspi.Registry.getDesktop(0)
        elements = []
        for i in range(desktop.childCount):
            app = desktop.getChildAtIndex(i)
            if app and app.name:
                elements.extend(self._walk_tree(app, app.name))
        return UIMap(
            screen_size=self._screen_size,
            elements=elements,
        )

    def _walk_tree(self, node, app_name: str, depth: int = 0) -> list[UIElement]:
        """Recursively walk AT-SPI tree."""
        elements = []
        try:
            bounds = None
            try:
                comp = node.queryComponent()
                rect = comp.getExtents(0)
                bounds = Bounds(x=rect.x, y=rect.y, width=rect.width, height=rect.height)
            except Exception:
                pass

            element = UIElement(
                id=f"{app_name}_{node.name or 'unnamed'}_{depth}",
                name=node.name or "",
                role=node.getRoleName(),
                bounds=bounds,
                app=app_name,
                metadata={"source": "atspi_fallback"},
            )
            elements.append(element)

            for i in range(node.childCount):
                elements.extend(self._walk_tree(node.getChildAtIndex(i), app_name, depth + 1))
        except Exception:
            pass
        return elements

    def get_active_window(self) -> Optional[UIElement]:
        """Get currently focused window."""
        desktop = pyatspi.Registry.getDesktop(0)
        for i in range(desktop.childCount):
            app = desktop.getChildAtIndex(i)
            if app and app.name:
                try:
                    state = app.getState()
                    if state.contains(pyatspi.STATE_ACTIVE):
                        return UIElement(
                            id=f"{app.name}_window",
                            name=app.name,
                            role="application",
                            app=app.name,
                        )
                except Exception:
                    pass
        return None

    def get_screen_size(self) -> Tuple[int, int]:
        return self._screen_size

    def _get_screen_size(self) -> Tuple[int, int]:
        try:
            import gi
            gi.require_version("Gdk", "4.0")
            from gi.repository import Gdk
            display = Gdk.Display.get_default()
            monitor = display.get_primary_monitor() or display.get_monitor(0)
            geometry = monitor.get_geometry()
            return (geometry.width, geometry.height)
        except Exception:
            return (1920, 1080)

    def find_element(
        self,
        role: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[UIElement]:
        """Find element by name/role."""
        ui_map = self.capture()
        for elem in ui_map.elements:
            match = True
            if name is not None and name.lower() not in elem.name.lower():
                match = False
            if role is not None and elem.role != role:
                match = False
            if match:
                return elem
        return None

    def get_stats(self) -> dict:
        total = self._vision_count + self._fallback_count
        return {
            "vision_queries": self._vision_count,
            "fallback_queries": self._fallback_count,
            "vision_rate": self._vision_count / max(1, total),
        }