"""Perception adapter that uses continuous video recording for silent capture."""

from __future__ import annotations

import os
import time
from typing import Optional

from aether.perception.base import PerceptionAdapter
from aether.perception.video_recorder import VideoRecorder
from aether.core.models import UIMap
from aether.perception.vision_first import VisionFirstPerceptionAdapter


class StreamingPerceptionAdapter(PerceptionAdapter):
    """Perception adapter using continuous video recording.

    Uses a background ffmpeg process to continuously capture the screen.
    Screenshots are instant (just reading the latest frame from memory)
    and completely silent (no portal notifications).

    Falls back to VisionFirstPerceptionAdapter if video recorder fails.
    """

    def __init__(
        self,
        recorder: Optional[VideoRecorder] = None,
        fallback: Optional[VisionFirstPerceptionAdapter] = None,
    ):
        self.recorder = recorder or VideoRecorder(width=320, fps=0.5)
        self.fallback = fallback
        self._started = False

    def start(self) -> None:
        """Start the background video recording."""
        if not self._started:
            self.recorder.start()
            self._started = True

    def stop(self) -> None:
        """Stop the background video recording."""
        if self._started:
            self.recorder.stop()
            self._started = False

    def capture(self) -> UIMap:
        """Capture current UI state using video frame."""
        if not self._started:
            self.start()

        try:
            # Get latest frame from video stream (instant, silent)
            frame_path = self.recorder.get_latest_frame()

            # Use the vision adapter on this frame
            # We create a temporary adapter just for analysis
            temp_adapter = VisionFirstPerceptionAdapter(
                vision_timeout=30,
                screenshot_scale=-1,  # Don't resize, already small
            )

            # Override screenshot capture to use our frame
            temp_adapter._capture_screenshot = lambda: frame_path

            return temp_adapter.capture()

        except Exception as e:
            print(f"  [Streaming] Video capture failed: {e}, using fallback")
            if self.fallback:
                return self.fallback.capture()
            raise

    def get_active_window(self):
        if self.fallback:
            return self.fallback.get_active_window()
        return None

    def get_screen_size(self):
        if self.fallback:
            return self.fallback.get_screen_size()
        return (1920, 1080)

    def find_element(self, role=None, name=None):
        if self.fallback:
            return self.fallback.find_element(role, name)
        return None

    def get_stats(self) -> dict:
        stats = self.recorder.get_stats()
        if self.fallback:
            stats["fallback_stats"] = self.fallback.get_stats()
        return stats