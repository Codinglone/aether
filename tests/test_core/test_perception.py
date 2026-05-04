from pathlib import Path

from aether.core.models import UIMap
from aether.perception.base import PerceptionAdapter
from tests.harness import MockPerceptionAdapter


class TestMockPerceptionAdapter:
    def test_loads_fixture(self):
        fixture_path = Path("tests/fixtures/calculator_linux.json")
        adapter = MockPerceptionAdapter(fixture_path)
        uimap = adapter.capture()
        assert isinstance(uimap, UIMap)
        assert uimap.screen_size == (1920, 1080)

    def test_finds_element_by_name(self):
        fixture_path = Path("tests/fixtures/calculator_linux.json")
        adapter = MockPerceptionAdapter(fixture_path)
        elem = adapter.find_element(role="push button", name="2")
        assert elem is not None
        assert elem.id == "btn2"

    def test_returns_none_for_missing_element(self):
        fixture_path = Path("tests/fixtures/calculator_linux.json")
        adapter = MockPerceptionAdapter(fixture_path)
        elem = adapter.find_element(role="push button", name="999")
        assert elem is None

    def test_get_active_window(self):
        fixture_path = Path("tests/fixtures/calculator_linux.json")
        adapter = MockPerceptionAdapter(fixture_path)
        win = adapter.get_active_window()
        assert win is not None
        assert win.name == "Calculator"

    def test_get_screen_size(self):
        fixture_path = Path("tests/fixtures/calculator_linux.json")
        adapter = MockPerceptionAdapter(fixture_path)
        size = adapter.get_screen_size()
        assert size == (1920, 1080)
