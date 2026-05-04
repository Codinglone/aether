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

        self._root.warp_pointer(x, y)
        self._display.sync()
        time.sleep(0.05)

        fake_input(self._display, X.ButtonPress, 1)
        self._display.sync()
        time.sleep(0.05)
        fake_input(self._display, X.ButtonRelease, 1)
        self._display.sync()
        time.sleep(0.05)

    def type_text(self, text: str) -> None:
        """Type text, handling shifted characters properly."""
        self._ensure_connected()
        from Xlib import X
        from Xlib.ext.xtest import fake_input
        import Xlib.XK

        SHIFT_CHARS = {
            '+': ('=', True), '*': ('8', True), '/': ('/', False),
            '-': ('-', False), '(': ('9', True), ')': ('0', True),
            '^': ('6', True), '%': ('5', True),
        }

        shift_keycode = self._display.keysym_to_keycode(Xlib.XK.XK_Shift_L)
        if not shift_keycode:
            shift_keycode = self._display.keysym_to_keycode(Xlib.XK.XK_Shift_R)

        for char in text:
            needs_shift = False
            base_char = char

            if char in SHIFT_CHARS:
                base_char, needs_shift = SHIFT_CHARS[char]
            elif char.isupper():
                base_char = char.lower()
                needs_shift = True

            keysym = ord(base_char)
            keycode = self._display.keysym_to_keycode(keysym)

            if keycode:
                if needs_shift and shift_keycode:
                    fake_input(self._display, X.KeyPress, shift_keycode)
                    self._display.sync()

                fake_input(self._display, X.KeyPress, keycode)
                self._display.sync()
                fake_input(self._display, X.KeyRelease, keycode)
                self._display.sync()

                if needs_shift and shift_keycode:
                    fake_input(self._display, X.KeyRelease, shift_keycode)
                    self._display.sync()

            time.sleep(0.05)

    def hotkey(self, modifiers: list[str], key: str) -> None:
        self._ensure_connected()
        from Xlib import X
        from Xlib.ext.xtest import fake_input
        import Xlib.XK

        mod_map = {
            "ctrl": Xlib.XK.XK_Control_L,
            "shift": Xlib.XK.XK_Shift_L,
            "alt": Xlib.XK.XK_Alt_L,
            "super": Xlib.XK.XK_Super_L,
        }

        mod_keycodes = []
        for mod in modifiers:
            mod_lower = mod.lower()
            if mod_lower in mod_map:
                kc = self._display.keysym_to_keycode(mod_map[mod_lower])
                if kc:
                    mod_keycodes.append(kc)

        keycode = None
        if len(key) == 1:
            keycode = self._display.keysym_to_keycode(ord(key))
        elif hasattr(Xlib.XK, f'XK_{key}'):
            keycode = self._display.keysym_to_keycode(getattr(Xlib.XK, f'XK_{key}'))

        if keycode:
            for kc in mod_keycodes:
                fake_input(self._display, X.KeyPress, kc)
                self._display.sync()

            fake_input(self._display, X.KeyPress, keycode)
            self._display.sync()
            fake_input(self._display, X.KeyRelease, keycode)
            self._display.sync()

            for kc in reversed(mod_keycodes):
                fake_input(self._display, X.KeyRelease, kc)
                self._display.sync()

    def scroll(self, x: int, y: int, delta: int) -> None:
        self._ensure_connected()
        from Xlib import X
        from Xlib.ext.xtest import fake_input

        self._root.warp_pointer(x, y)
        self._display.sync()

        button = 4 if delta > 0 else 5
        for _ in range(abs(delta)):
            fake_input(self._display, X.ButtonPress, button)
            self._display.sync()
            fake_input(self._display, X.ButtonRelease, button)
            self._display.sync()

    def alt_tab(self) -> None:
        """Press Alt+Tab to switch window focus."""
        self.hotkey(["alt"], "Tab")
        time.sleep(0.3)

    def focus_window_by_name(self, name_substring: str) -> bool:
        """Find and focus an X11 window by name substring."""
        self._ensure_connected()
        from Xlib import X

        # Search all windows recursively
        def search_window(window, depth=0):
            try:
                wm_name = window.get_wm_name()
                if wm_name and name_substring.lower() in str(wm_name).lower():
                    return window
            except:
                pass
            
            try:
                tree = window.query_tree()
                for child in tree.children:
                    found = search_window(child, depth + 1)
                    if found:
                        return found
            except:
                pass
            return None

        target = search_window(self._root)
        if target:
            try:
                # Raise window and set focus
                target.configure(stack_mode=X.Above)
                self._display.sync()
                self._display.set_input_focus(target, X.RevertToParent, X.CurrentTime)
                self._display.sync()
                time.sleep(0.3)
                return True
            except Exception:
                pass
        return False
