from __future__ import annotations

from typing import Optional, Tuple

from aether.core.models import Action


class SafetyChecker:
    SHELL_BLACKLIST = {"rm", "sudo", "mkfs", "dd", "format", "fdisk"}
    MAX_CLICK_X = 7680
    MAX_CLICK_Y = 4320
    MAX_TYPE_LENGTH = 10000
    MAX_SHELL_TIMEOUT = 60

    def check(self, action: Action) -> Tuple[bool, Optional[str]]:
        if action.type == "shell":
            return self._check_shell(action)
        elif action.type == "click":
            return self._check_click(action)
        elif action.type == "type":
            return self._check_type(action)
        elif action.type in ("hotkey", "wait", "scroll"):
            return True, None
        else:
            return False, f"Unknown action type: {action.type}"

    def _check_shell(self, action: Action) -> Tuple[bool, Optional[str]]:
        command = action.params.get("command", "")
        parts = command.split()
        if not parts:
            return False, "Empty shell command"
        for part in parts:
            clean = part.strip(";|&><")
            if clean in self.SHELL_BLACKLIST:
                return False, f"Blacklisted command: {clean}"
        timeout = action.params.get("timeout", self.MAX_SHELL_TIMEOUT)
        if timeout > self.MAX_SHELL_TIMEOUT:
            return False, f"Timeout {timeout}s exceeds max {self.MAX_SHELL_TIMEOUT}s"
        return True, None

    def _check_click(self, action: Action) -> Tuple[bool, Optional[str]]:
        x = action.params.get("x", 0)
        y = action.params.get("y", 0)
        if x < 0 or x > self.MAX_CLICK_X:
            return False, f"Click x={x} out of bounds [0, {self.MAX_CLICK_X}]"
        if y < 0 or y > self.MAX_CLICK_Y:
            return False, f"Click y={y} out of bounds [0, {self.MAX_CLICK_Y}]"
        return True, None

    def _check_type(self, action: Action) -> Tuple[bool, Optional[str]]:
        text = action.params.get("text", "")
        if len(text) > self.MAX_TYPE_LENGTH:
            return False, f"Type text length {len(text)} exceeds max {self.MAX_TYPE_LENGTH}"
        return True, None
