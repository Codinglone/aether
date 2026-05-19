"""Real-time verifier for desktop automation."""

from __future__ import annotations

import os
import subprocess

from aether.core.models import UIMap, Action, VerificationResult
from aether.core.verify import Verifier


class DesktopVerifier(Verifier):
    """Verifier that checks actual desktop state.

    Strategies:
    1. Process check: is the target app running?
    2. Audio check: is sound playing?
    3. Screenshot diff: did the screen change?
    4. Window check: did active window change?
    """

    def __init__(self):
        self._last_screenshot_brightness = 0.0

    def verify(self, before: UIMap, after: UIMap, action: Action) -> VerificationResult:
        # Strategy 1: Check if relevant process is running after shell/open actions
        if action.type in ("shell", "click"):
            proc_result = self._check_process_running(action)
            if proc_result:
                return proc_result

        # Strategy 2: Check audio for media-related actions
        if action.type in ("click", "key") and self._is_media_action(action):
            audio_result = self._check_audio_playing()
            if audio_result:
                return audio_result

        # Strategy 3: Screenshot brightness diff
        bright_result = self._check_brightness_change()
        if bright_result:
            return bright_result

        # Strategy 4: Window change
        window_result = self._check_window_change(before, after)
        if window_result:
            return window_result

        # Default: assume success but low confidence
        return VerificationResult(
            success=True,
            confidence=0.3,
            matched_strategy="default",
            details="No strong verification signal, assuming success",
        )

    def _check_process_running(self, action: Action) -> VerificationResult | None:
        """Check if relevant process is running."""
        # Infer app from action reason or params
        reason = action.reason.lower()
        app_checks = {
            "brave": "brave",
            "firefox": "firefox",
            "chrome": "chrome",
            "spotify": "spotify",
            "terminal": "gnome-terminal",
        }

        for keyword, process_name in app_checks.items():
            if keyword in reason:
                result = subprocess.run(
                    ["pgrep", "-f", process_name],
                    capture_output=True,
                    timeout=2,
                )
                if result.returncode == 0:
                    return VerificationResult(
                        success=True,
                        confidence=0.9,
                        matched_strategy="process_running",
                        details=f"{process_name} is running",
                    )
                else:
                    return VerificationResult(
                        success=False,
                        confidence=0.7,
                        matched_strategy="process_running",
                        details=f"{process_name} not found",
                    )
        return None

    def _is_media_action(self, action: Action) -> bool:
        """Check if action is likely related to media playback."""
        reason = action.reason.lower()
        media_keywords = ["play", "pause", "video", "audio", "music", "youtube"]
        return any(kw in reason for kw in media_keywords)

    def _check_audio_playing(self) -> VerificationResult | None:
        """Check if any audio stream is active."""
        try:
            result = subprocess.run(
                ["pactl", "list", "sink-inputs"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and "Sink Input" in result.stdout:
                # Count sink inputs
                count = result.stdout.count("Sink Input")
                return VerificationResult(
                    success=True,
                    confidence=min(1.0, 0.5 + 0.1 * count),
                    matched_strategy="audio_playing",
                    details=f"{count} audio stream(s) active",
                )
        except Exception:
            pass
        return None

    def _check_brightness_change(self) -> VerificationResult | None:
        """Check if screen brightness changed (indicates visual change)."""
        try:
            from PIL import Image
            import glob

            # Find latest screenshot
            files = (
                glob.glob("/tmp/aether_vision_*.png")
                + glob.glob(os.path.expanduser("~/Pictures/Screenshot*.png"))
            )
            if not files:
                return None

            latest = max(files, key=os.path.getmtime)
            img = Image.open(latest)
            pixels = list(img.getdata())
            avg = sum(sum(p[:3]) for p in pixels) / (len(pixels) * 3)

            if abs(avg - self._last_screenshot_brightness) > 5.0:
                diff = abs(avg - self._last_screenshot_brightness)
                self._last_screenshot_brightness = avg
                return VerificationResult(
                    success=True,
                    confidence=min(1.0, 0.5 + diff / 50.0),
                    matched_strategy="brightness_change",
                    details=f"Brightness changed by {diff:.1f}",
                )

            self._last_screenshot_brightness = avg
        except Exception:
            pass
        return None

    def _check_window_change(self, before: UIMap, after: UIMap) -> VerificationResult | None:
        if before.active_window != after.active_window:
            return VerificationResult(
                success=True,
                confidence=0.8,
                matched_strategy="window_change",
                details="Active window changed",
            )
        return None


class AudioVerifier(DesktopVerifier):
    """Verifier focused on audio playback detection."""

    def verify(self, before: UIMap, after: UIMap, action: Action) -> VerificationResult:
        audio = self._check_audio_playing()
        if audio:
            return audio
        return VerificationResult(
            success=False,
            confidence=0.0,
            matched_strategy="audio",
            details="No audio detected",
        )