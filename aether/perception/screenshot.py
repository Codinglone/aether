"""Screenshot capture for Linux using available tools."""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional


class ScreenshotCapture:
    """Capture screenshots using the best available backend.
    
    Priority:
    1. ffmpeg (x11grab) - works via XWayland
    2. grim - native Wayland (if compositor supports it)
    3. PIL ImageGrab - X11 fallback
    """

    def __init__(self):
        self._backend = self._detect_backend()
        self._last_capture_time = 0.0
        self._cache_duration = 0.5  # Don't re-capture within 500ms

    def _detect_backend(self) -> str:
        """Detect the best screenshot backend."""
        if self._has_command("ffmpeg"):
            return "ffmpeg"
        if self._has_command("grim"):
            return "grim"
        try:
            from PIL import ImageGrab
            return "pil"
        except ImportError:
            pass
        raise RuntimeError("No screenshot backend available (install ffmpeg, grim, or Pillow)")

    @staticmethod
    def _has_command(cmd: str) -> bool:
        return subprocess.run(
            ["which", cmd], capture_output=True, check=False
        ).returncode == 0

    def capture(self, output_path: Optional[str] = None) -> str:
        """Capture a screenshot and save to output_path.
        
        Returns the path to the saved screenshot.
        """
        # Cache: don't re-capture too quickly
        now = time.time()
        if now - self._last_capture_time < self._cache_duration:
            time.sleep(self._cache_duration - (now - self._last_capture_time))

        if output_path is None:
            output_path = f"/tmp/aether_screenshot_{int(time.time())}.png"

        if self._backend == "ffmpeg":
            self._capture_ffmpeg(output_path)
        elif self._backend == "grim":
            self._capture_grim(output_path)
        elif self._backend == "pil":
            self._capture_pil(output_path)

        self._last_capture_time = time.time()
        return output_path

    def _capture_ffmpeg(self, output_path: str) -> None:
        """Capture using ffmpeg x11grab."""
        display = os.environ.get("DISPLAY", ":0")
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "x11grab",
                "-i", display,
                "-vframes", "1",
                "-update", "1",
                output_path,
            ],
            capture_output=True,
            check=False,
            timeout=10,
        )
        if result.returncode != 0:
            error = result.stderr.decode("utf-8", errors="ignore")[-200:]
            raise RuntimeError(f"ffmpeg screenshot failed: {error}")

    def _capture_grim(self, output_path: str) -> None:
        """Capture using grim (Wayland-native)."""
        result = subprocess.run(
            ["grim", output_path],
            capture_output=True,
            check=False,
            timeout=10,
        )
        if result.returncode != 0:
            error = result.stderr.decode("utf-8", errors="ignore")
            raise RuntimeError(f"grim screenshot failed: {error}")

    def _capture_pil(self, output_path: str) -> None:
        """Capture using PIL ImageGrab."""
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save(output_path)

    def get_screen_size(self) -> tuple[int, int]:
        """Get the actual screen size in pixels."""
        if self._backend == "ffmpeg":
            # Capture a screenshot and check its dimensions
            path = self.capture()
            from PIL import Image
            with Image.open(path) as img:
                return img.size
        elif self._backend == "grim":
            path = self.capture()
            from PIL import Image
            with Image.open(path) as img:
                return img.size
        else:
            # Try Gdk
            try:
                import gi
                gi.require_version('Gdk', '4.0')
                from gi.repository import Gdk
                display = Gdk.Display.get_default()
                monitor = display.get_primary_monitor() or display.get_monitor(0)
                geometry = monitor.get_geometry()
                return (geometry.width, geometry.height)
            except Exception:
                return (1920, 1080)
