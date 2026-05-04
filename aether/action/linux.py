from __future__ import annotations

import time
from aether.action.base import ActionAdapter


class LinuxActionAdapter(ActionAdapter):
    """Linux action adapter using X11 via python-xlib (works through XWayland)."""

    def __init__(self):
        self._display = None
        self._root = None
        self._connect()

    def _connect(self):
        try:
            from Xlib.display import Display
            self._display = Display()
            self._root = self._display.screen().root
        except Exception:
            self._display = None
            self._root = None

    def _ensure_connected(self):
        if self._display is None:
            self._connect()
        if self._display is None:
            raise RuntimeError("Cannot connect to X11 display. Is XWayland running?")

    def click(self, x: int, y: int) -> None:
        self._ensure_connected()
        from Xlib.ext.xtest import fake_input
        from Xlib import X

        # Move to position
        self._root.warp_pointer(x, y)
        self._display.sync()
        time.sleep(0.05)

        # Press and release left button
        fake_input(self._display, X.ButtonPress, 1)
        self._display.sync()
        time.sleep(0.05)
        fake_input(self._display, X.ButtonRelease, 1)
        self._display.sync()
        time.sleep(0.05)

    def type_text(self, text: str) -> None:
        self._ensure_connected()
        from Xlib.ext.xtest import fake_input
        from Xlib import X

        for char in text:
            # Simple ASCII typing
            if char.isalpha():
                keycode = self._display.keysym_to_keycode(ord(char))
                if keycode:
                    fake_input(self._display, X.KeyPress, keycode)
                    self._display.sync()
                    fake_input(self._display, X.KeyRelease, keycode)
                    self._display.sync()
            elif char == ' ':
                keycode = self._display.keysym_to_keycode(0x0020)
                if keycode:
                    fake_input(self._display, X.KeyPress, keycode)
                    self._display.sync()
                    fake_input(self._display, X.KeyRelease, keycode)
                    self._display.sync()
            time.sleep(0.01)

    def hotkey(self, modifiers: list[str], key: str) -> None:
        self._ensure_connected()
        from Xlib.ext.xtest import fake_input
        from Xlib import X

        mod_map = {
            "ctrl": X.ControlMask,
            "shift": X.ShiftMask,
            "alt": X.Mod1Mask,
            "super": X.Mod4Mask,
        }

        # Get modifier keycodes
        mod_keycodes = []
        for mod in modifiers:
            mod_lower = mod.lower()
            if mod_lower in mod_map:
                # Find a keycode for this modifier
                # This is a simplification - proper implementation would use XKB
                pass

        # Get key keycode
        keycode = None
        if len(key) == 1:
            keycode = self._display.keysym_to_keycode(ord(key))

        if keycode:
            fake_input(self._display, X.KeyPress, keycode)
            self._display.sync()
            fake_input(self._display, X.KeyRelease, keycode)
            self._display.sync()

    def scroll(self, x: int, y: int, delta: int) -> None:
        self._ensure_connected()
        from Xlib.ext.xtest import fake_input
        from Xlib import X

        self._root.warp_pointer(x, y)
        self._display.sync()

        button = 4 if delta > 0 else 5  # 4 = scroll up, 5 = scroll down
        for _ in range(abs(delta)):
            fake_input(self._display, X.ButtonPress, button)
            self._display.sync()
            fake_input(self._display, X.ButtonRelease, button)
            self._display.sync()
