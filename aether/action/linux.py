from __future__ import annotations

import os
import subprocess
import time
from aether.action.base import ActionAdapter


class LinuxActionAdapter(ActionAdapter):
    """Linux action adapter supporting both X11 (python-xlib) and Wayland (ydotool)."""

    def __init__(self):
        self._display = None
        self._root = None
        self._ydotool_socket = None
        self._wayland = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        self._connect()

    def _connect(self):
        # Try X11 display connection
        try:
            from Xlib.display import Display
            self._display = Display()
            self._root = self._display.screen().root
        except Exception:
            self._display = None
            self._root = None

        # Detect ydotool socket for Wayland
        self._ydotool_socket = self._find_ydotool_socket()

    def _find_ydotool_socket(self) -> str | None:
        """Find the ydotool daemon socket."""
        candidates = [
            os.environ.get("YDOTOOL_SOCKET"),
            "/tmp/.ydotool_socket",
            f"/run/user/{os.getuid()}/.ydotool_socket",
        ]
        for path in candidates:
            if path and os.path.exists(path) and os.access(path, os.R_OK | os.W_OK):
                return path
        return None

    def _ydotool(self, *args: str) -> bool:
        """Run a ydotool command. Returns True on success."""
        if not self._ydotool_socket:
            return False
        env = os.environ.copy()
        env["YDOTOOL_SOCKET"] = self._ydotool_socket
        try:
            result = subprocess.run(
                ["ydotool", *args],
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _ensure_connected(self):
        if self._display is None:
            self._connect()
        if self._display is None and not self._ydotool_socket:
            raise RuntimeError(
                "Cannot connect to X11 display or ydotool. "
                "Is XWayland running or ydotoold started?"
            )

    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> None:
        """Move mouse to (x, y), optionally animating over `duration` seconds."""
        if self._ydotool_socket:
            if duration > 0:
                # Animate: we don't know current position, so we do small steps
                # from the last known position or from screen center
                steps = max(int(duration * 20), 1)  # 20 steps per second
                # Simple approach: just move directly (ydotool is fast)
                # For visual effect, add small delays
                for _ in range(steps):
                    self._ydotool("mousemove", str(x), str(y))
                    time.sleep(duration / steps)
            else:
                self._ydotool("mousemove", str(x), str(y))
                time.sleep(0.02)
        elif self._display:
            from Xlib import X
            if duration > 0 and self._root:
                # Get current position
                root_x = root_y = 0
                try:
                    pointer = self._root.query_pointer()
                    root_x, root_y = pointer.root_x, pointer.root_y
                except Exception:
                    root_x = root_y = 0
                steps = max(int(duration * 20), 1)
                for i in range(1, steps + 1):
                    t = i / steps
                    cur_x = int(root_x + (x - root_x) * t)
                    cur_y = int(root_y + (y - root_y) * t)
                    self._root.warp_pointer(cur_x, cur_y)
                    self._display.sync()
                    time.sleep(duration / steps)
            else:
                self._root.warp_pointer(x, y)
                self._display.sync()
                time.sleep(0.02)

    def click(self, x: int, y: int) -> None:
        """Move mouse to (x, y) and click left button."""
        self.move_mouse(x, y)
        time.sleep(0.05)
        if self._ydotool_socket:
            self._ydotool("click", "0xC0")  # left button down+up
            time.sleep(0.05)
        elif self._display:
            # Use X11
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
        else:
            raise RuntimeError("No input backend available")

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
        if self._ydotool_socket:
            self._ydotool("mousemove", str(x), str(y))
            time.sleep(0.05)
            # ydotool doesn't have direct scroll, use click on scroll buttons
            # 0x40 = scroll up, 0x80 = scroll down (these are actually wheel events)
            # ydotool click doesn't support scroll wheel well, skip for now
        elif self._display:
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
        else:
            raise RuntimeError("No input backend available")

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
