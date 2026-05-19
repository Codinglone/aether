"""Wayland-native action adapter using ydotool."""

from __future__ import annotations

import os
import subprocess
import time

from aether.action.base import ActionAdapter


class YdotoolActionAdapter(ActionAdapter):
    """Action adapter for Wayland using ydotool.

    Requires ydotoold daemon running with accessible socket.
    Set YDOTOOL_SOCKET env var or pass socket_path.

    Supports: click, right_click, type, hotkey, scroll, wait.
    """

    def __init__(self, socket_path: str = "/tmp/.ydotool_socket"):
        self.socket_path = socket_path
        self._env = {**os.environ, "YDOTOOL_SOCKET": socket_path}
        self._screen_size = self._get_screen_size()

    def click(self, x: int, y: int) -> None:
        self._ydotool("mousemove", "--absolute", str(x), str(y))
        time.sleep(0.08)
        self._ydotool("click", "0xC0")
        time.sleep(0.15)

    def right_click(self, x: int, y: int) -> None:
        self._ydotool("mousemove", "--absolute", str(x), str(y))
        time.sleep(0.08)
        self._ydotool("click", "0xC1")
        time.sleep(0.15)

    def type_text(self, text: str) -> None:
        self._ydotool("type", text)
        time.sleep(0.3)

    def key(self, keyname: str) -> None:
        """Press a single key or key combo string. E.g. key('Return'), key('ctrl+t')."""
        self._ydotool("key", keyname)
        time.sleep(0.3)

    def hotkey(self, modifiers: list[str], key: str) -> None:
        """Press hotkey combination. E.g. hotkey(['ctrl', 'alt'], 't')."""
        # ydotool key format: ctrl+alt+t
        parts = []
        for mod in modifiers:
            parts.append(mod.lower())
        parts.append(key)
        combo = "+".join(parts)
        self._ydotool("key", combo)
        time.sleep(0.3)

    def scroll(self, x: int, y: int, delta: int = 3) -> None:
        self._ydotool("mousemove", "--absolute", str(x), str(y))
        time.sleep(0.1)
        # Scroll down: 0xC8, up: 0xC7
        button = "0xC8" if delta > 0 else "0xC7"
        clicks = abs(delta)
        for _ in range(clicks):
            self._ydotool("click", button)
            time.sleep(0.05)

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)

    def _ydotool(self, *args: str) -> None:
        subprocess.run(["ydotool", *args], env=self._env, check=True, timeout=5)

    def _get_screen_size(self) -> tuple[int, int]:
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