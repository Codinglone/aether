from pathlib import Path

from aether.macro.models import ElementSelector, Intent, Macro
from aether.macro.recorder import MacroRecorder
from aether.core.models import Action
from tests.harness import MockPerceptionAdapter, MockActionAdapter
from aether.macro.player import MacroPlayer


class TestMacroRecorder:
    def test_start_stop_creates_macro(self):
        recorder = MacroRecorder()
        recorder.start_recording("test macro")
        recorder.stop_recording()
        assert recorder.current_macro is None

    def test_records_intent(self):
        recorder = MacroRecorder()
        recorder.start_recording("test")
        action = Action(
            type="click",
            params={"x": 100, "y": 200},
            reason="Click Save",
            expected_change="Dialog opens",
        )
        recorder.record_action(action, element_name="Save", element_role="push button")
        macro = recorder.stop_recording()
        assert macro is not None
        assert len(macro.intents) == 1
        assert macro.intents[0].target.name == "Save"

    def test_intent_has_selector(self):
        recorder = MacroRecorder()
        recorder.start_recording("test")
        action = Action(
            type="type",
            params={"text": "hello"},
            reason="Type greeting",
            expected_change="Text appears",
        )
        recorder.record_action(action, element_name="Input", element_role="text")
        macro = recorder.stop_recording()
        intent = macro.intents[0]
        assert intent.target.role == "text"
        assert intent.target.name == "Input"


class TestMacroPlayer:
    def test_plays_macro_by_name(self):
        fixture = Path("tests/fixtures/calculator_linux.json")
        perception = MockPerceptionAdapter(fixture)
        action = MockActionAdapter()
        player = MacroPlayer(perception, action)

        macro = Macro(
            name="click two",
            intents=[
                Intent(
                    action_type="click",
                    target=ElementSelector(role="push button", name="2"),
                    params={},
                )
            ],
        )
        player.play(macro)
        assert len(action.executed_actions) == 1
        assert action.executed_actions[0]["type"] == "click"

    def test_self_heal_finds_by_role(self):
        fixture = Path("tests/fixtures/calculator_linux.json")
        perception = MockPerceptionAdapter(fixture)
        action = MockActionAdapter()
        player = MacroPlayer(perception, action)

        # Target by wrong name, but correct role exists
        macro = Macro(
            name="click something",
            intents=[
                Intent(
                    action_type="click",
                    target=ElementSelector(role="push button", name="NonExistent"),
                    params={},
                )
            ],
        )
        player.play(macro)
        # Should fall back to fuzzy find by role
        assert len(action.executed_actions) == 1
