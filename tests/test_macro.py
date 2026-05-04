from aether.macro.models import ElementSelector, Intent, Macro
from aether.macro.recorder import MacroRecorder
from aether.core.models import Action


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
