from aether.core.models import UIMap, UIElement, Bounds, Action
from aether.core.verify import Verifier


class TestVerifier:
    def _make_uimap(self, name: str) -> UIMap:
        return UIMap(
            screen_size=(1920, 1080),
            elements=[
                UIElement(
                    id="display",
                    role="text",
                    name=name,
                    bounds=Bounds(x=0, y=0, width=100, height=30),
                    state=set(),
                )
            ],
        )

    def test_detects_state_change(self):
        before = self._make_uimap("0")
        after = self._make_uimap("2")
        action = Action(
            type="click",
            params={"x": 50, "y": 15},
            reason="Click button 2",
            expected_change="Display changes to 2",
        )
        verifier = Verifier()
        result = verifier.verify(before, after, action)
        assert result.success is True
        assert result.confidence > 0.5

    def test_no_change_fails(self):
        before = self._make_uimap("0")
        after = self._make_uimap("0")
        action = Action(
            type="click",
            params={"x": 50, "y": 15},
            reason="Click button",
            expected_change="Display should change",
        )
        verifier = Verifier()
        result = verifier.verify(before, after, action)
        assert result.success is False

    def test_focus_change_detected(self):
        before = UIMap(
            screen_size=(1920, 1080),
            elements=[
                UIElement(
                    id="btn1",
                    role="push button",
                    name="One",
                    bounds=Bounds(x=0, y=0, width=50, height=30),
                    state=set(),
                )
            ],
            focused_element=None,
        )
        after = UIMap(
            screen_size=(1920, 1080),
            elements=[
                UIElement(
                    id="btn1",
                    role="push button",
                    name="One",
                    bounds=Bounds(x=0, y=0, width=50, height=30),
                    state=set(),
                )
            ],
            focused_element=UIElement(
                id="btn1",
                role="push button",
                name="One",
                bounds=Bounds(x=0, y=0, width=50, height=30),
                state=set(),
            ),
        )
        action = Action(
            type="click",
            params={"x": 25, "y": 15},
            reason="Click button",
            expected_change="Button gains focus",
        )
        verifier = Verifier()
        result = verifier.verify(before, after, action)
        assert result.success is True
        assert result.matched_strategy == "focus"
