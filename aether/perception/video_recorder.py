"""Continuous screen recording using ffmpeg for silent frame capture.

Note: On Wayland sessions, ffmpeg x11grab may capture black screens
for native Wayland apps. The portal fallback is used in that case.

For X11 or XWayland apps, this works silently without notifications."""

from __future__ import annotations

import glob
import os
import subprocess
import time
from typing import Optional


class VideoRecorder:
    """Continuous screen recorder using ffmpeg.

    Runs ffmpeg in the background, continuously overwriting a single
    JPEG file. Screenshots are instant (just read the file) and
    silent for X11/XWayland content.

    For pure Wayland apps, falls back to portal capture (which may
    trigger notifications).

    Usage:
        recorder = VideoRecorder(frame_path="/tmp/latest_frame.jpg")
        recorder.start()
        # ... later ...
        frame_path = recorder.get_latest_frame()
        # ... when done ...
        recorder.stop()
    """

    def __init__(
        self,
        display: str = ":0",
        width: int = 320,
        fps: float = 0.5,
        quality: int = 5,
        frame_path: str = "/tmp/aether_latest_frame.jpg",
    ):
        self.display = display
        self.width = width
        self.fps = fps
        self.quality = quality
        self.frame_path = frame_path
        self._process: Optional[subprocess.Popen] = None
        self._running = False
        self._start_time: Optional[float] = None
        self._using_portal = False

    def start(self) -> None:
        """Start the background recording."""
        if self._running:
            return

        print(f"[VideoRecorder] Starting at {self.width}px, {self.fps} fps")

        # Remove old frame
        if os.path.exists(self.frame_path):
            os.remove(self.frame_path)

        # Try ffmpeg x11grab first (silent)
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "x11grab",
            "-i", self.display,
            "-vf", f"fps={self.fps},scale={self.width}:-1",
            "-q:v", str(self.quality),
            "-update", "1",
            self.frame_path,
        ]

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self._running = True
        self._start_time = time.time()

        # Wait for first frame
        for _ in range(50):
            if os.path.exists(self.frame_path) and os.path.getsize(self.frame_path) > 100:
                # Check if it's not black
                if self._is_frame_valid():
                    print(f"[VideoRecorder] ffmpeg x11grab working (silent)")
                    return
                else:
                    print(f"[VideoRecorder] x11grab dark, switching to portal...")
                    self._switch_to_portal()
                    return
            time.sleep(0.1)

        print(f"[VideoRecorder] Warning: no frame received, using portal")
        self._switch_to_portal()

    def _switch_to_portal(self) -> None:
        """Switch to portal-based capture for Wayland."""
        self._using_portal = True
        if self._process:
            self._process.terminate()
            self._process = None

        # Portal captures will be handled by _capture_via_portal
        # We just need to take portal screenshots periodically
        print(f"[VideoRecorder] Using GNOME portal (may trigger notifications)")

    def _capture_via_portal(self) -> Optional[str]:
        """Use freedesktop portal for screenshot."""
        pictures_dir = os.path.expanduser("~/Pictures")
        for f in glob.glob(os.path.join(pictures_dir, "Screenshot*.png")):
            try:
                os.remove(f)
            except OSError:
                pass

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

        for _ in range(20):
            time.sleep(0.3)
            files = glob.glob(os.path.join(pictures_dir, "Screenshot*.png"))
            if files:
                # Resize if needed
                if self.width > 0:
                    resized = self.frame_path
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", files[0], "-vf",
                         f"scale={self.width}:-1",
                         "-vframes", "1", "-update", "1", resized],
                        capture_output=True, timeout=10,
                    )
                    if os.path.exists(resized):
                        return resized
                return files[0]
        return None

    def _is_frame_valid(self, min_brightness: float = 5.0) -> bool:
        """Check if captured frame is not mostly black."""
        try:
            from PIL import Image
            with Image.open(self.frame_path) as img:
                pixels = list(img.getdata())
                if img.mode in ("RGB", "RGBA"):
                    avg = sum(sum(p[:3]) for p in pixels) / (len(pixels) * 3)
                else:
                    avg = sum(pixels) / len(pixels)
                return avg > min_brightness
        except Exception:
            return False

    def stop(self) -> None:
        """Stop the background recording."""
        self._running = False
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
        print(f"[VideoRecorder] Stopped")

    def get_latest_frame(self) -> str:
        """Get the path to the latest frame."""
        if not self._running:
            raise RuntimeError("Recorder not running")

        if self._using_portal:
            # Trigger a new portal capture
            path = self._capture_via_portal()
            if path:
                return path
            raise RuntimeError("Portal capture failed")

        if not os.path.exists(self.frame_path):
            raise RuntimeError("No frame available yet")

        return self.frame_path

    def get_stats(self) -> dict:
        """Get recording statistics."""
        elapsed = time.time() - (self._start_time or time.time())
        frame_size = os.path.getsize(self.frame_path) if os.path.exists(self.frame_path) else 0
        return {
            "running": self._running,
            "using_portal": self._using_portal,
            "elapsed_seconds": elapsed,
            "frame_size_kb": frame_size // 1024,
            "frame_path": self.frame_path,
        }