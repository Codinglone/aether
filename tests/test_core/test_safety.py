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
