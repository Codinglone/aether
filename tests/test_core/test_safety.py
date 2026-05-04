import pytest
from aether.core.models import Action
from aether.core.safety import SafetyChecker


class TestSafetyChecker:
    def test_allows_safe_click(self):
        checker = SafetyChecker()
        action = Action(
            type="click",
            params={"x": 100, "y": 200},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is True
        assert error is None

    def test_rejects_blacklisted_shell_command(self):
        checker = SafetyChecker()
        action = Action(
            type="shell",
            params={"command": "rm -rf /"},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False
        assert "rm" in (error or "")

    def test_rejects_sudo(self):
        checker = SafetyChecker()
        action = Action(
            type="shell",
            params={"command": "sudo apt update"},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False
        assert "sudo" in (error or "")

    def test_rejects_empty_shell_command(self):
        checker = SafetyChecker()
        action = Action(
            type="shell",
            params={"command": ""},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False
        assert "Empty shell command" in (error or "")

    def test_rejects_shell_timeout_exceeded(self):
        checker = SafetyChecker()
        action = Action(
            type="shell",
            params={"command": "sleep 1", "timeout": 61},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False
        assert "Timeout" in (error or "")

    def test_allows_safe_shell_command(self):
        checker = SafetyChecker()
        action = Action(
            type="shell",
            params={"command": "ls -la"},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is True
        assert error is None

    def test_allows_hotkey(self):
        checker = SafetyChecker()
        action = Action(
            type="hotkey",
            params={"keys": ["ctrl", "c"]},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is True
        assert error is None

    def test_allows_wait(self):
        checker = SafetyChecker()
        action = Action(
            type="wait",
            params={"duration": 1},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is True
        assert error is None

    def test_allows_scroll(self):
        checker = SafetyChecker()
        action = Action(
            type="scroll",
            params={"direction": "down"},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is True
        assert error is None

    def test_rejects_unknown_action_type(self):
        checker = SafetyChecker()
        action = Action(
            type="unknown",
            params={},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False
        assert "Unknown action type" in (error or "")

    def test_rejects_negative_click_x(self):
        checker = SafetyChecker()
        action = Action(
            type="click",
            params={"x": -1, "y": 100},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False
        assert "x=-1" in (error or "")

    def test_rejects_out_of_bounds_click_y(self):
        checker = SafetyChecker()
        action = Action(
            type="click",
            params={"x": 100, "y": 99999},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False
        assert "y=99999" in (error or "")

    def test_rejects_out_of_bounds_click(self):
        checker = SafetyChecker()
        action = Action(
            type="click",
            params={"x": 99999, "y": 100},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False

    def test_rejects_long_type_text(self):
        checker = SafetyChecker()
        action = Action(
            type="type",
            params={"text": "x" * 20000},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False
