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
        self._last_mouse_x = None
        self._last_mouse_y = None
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
        self._ensure_connected()
        
        if duration > 0:
            # Animate the movement
            steps = max(int(duration * 30), 1)  # 30 steps per second for smooth animation
            
            # Get current position
            if self._last_mouse_x is not None and self._last_mouse_y is not None:
                start_x, start_y = self._last_mouse_x, self._last_mouse_y
            elif self._display and self._root:
                try:
                    pointer = self._root.query_pointer()
                    start_x, start_y = pointer.root_x, pointer.root_y
                except Exception:
                    start_x, start_y = 960, 540  # Default to screen center
            else:
                start_x, start_y = 960, 540
            
            # Interpolate and move
            for i in range(1, steps + 1):
                t = i / steps
                cur_x = int(start_x + (x - start_x) * t)
                cur_y = int(start_y + (y - start_y) * t)
                
                if self._ydotool_socket:
                    self._ydotool("mousemove", "--absolute", str(cur_x), str(cur_y))
                elif self._display:
                    self._root.warp_pointer(cur_x, cur_y)
                    self._display.sync()
                
                time.sleep(duration / steps)
        else:
            # Instant move
            if self._ydotool_socket:
                self._ydotool("mousemove", "--absolute", str(x), str(y))
            elif self._display:
                self._root.warp_pointer(x, y)
                self._display.sync()
        
        # Update tracked position
        self._last_mouse_x = x
        self._last_mouse_y = y

    def click(self, x: int, y: int) -> None:
        """Move mouse to (x, y) and click left button."""
        self.move_mouse(x, y)
        time.sleep(0.05)
        if self._ydotool_socket:
            self._ydotool("click", "0xC0")  # left button down+up
            time.sleep(0.05)
        elif self._display:
            from Xlib.ext.xtest import fake_input
            from Xlib import X

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
            self.move_mouse(x, y)
            time.sleep(0.05)
            # ydotool wheel: positive = up, negative = down
            for _ in range(abs(delta)):
                if delta > 0:
                    self._ydotool("mousemove", "--wheel", "0", "1")
                else:
                    self._ydotool("mousemove", "--wheel", "0", "-1")
                time.sleep(0.05)
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
