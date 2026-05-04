from aether.action.base import ActionAdapter
from tests.harness import MockActionAdapter


class TestMockActionAdapter:
    def test_click_records_action(self):
        adapter = MockActionAdapter()
        adapter.click(100, 200)
        assert len(adapter.executed_actions) == 1
        assert adapter.executed_actions[0]["type"] == "click"
        assert adapter.executed_actions[0]["x"] == 100

    def test_type_records_action(self):
        adapter = MockActionAdapter()
        adapter.type_text("hello")
        assert len(adapter.executed_actions) == 1
        assert adapter.executed_actions[0]["type"] == "type"
        assert adapter.executed_actions[0]["text"] == "hello"

    def test_hotkey_records_action(self):
        adapter = MockActionAdapter()
        adapter.hotkey(["ctrl"], "s")
        assert len(adapter.executed_actions) == 1
        assert adapter.executed_actions[0]["type"] == "hotkey"

    def test_scroll_records_action(self):
        adapter = MockActionAdapter()
        adapter.scroll(100, 200, -3)
        assert len(adapter.executed_actions) == 1
        assert adapter.executed_actions[0]["type"] == "scroll"

    def test_clear_actions(self):
        adapter = MockActionAdapter()
        adapter.click(1, 2)
        adapter.clear()
        assert len(adapter.executed_actions) == 0
