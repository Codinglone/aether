from aether.core.models import UIMap, UIElement, Bounds, ActionPlan
from aether.core.brain import StubBrain


class TestStubBrain:
    def test_returns_action_plan(self):
        brain = StubBrain()
        uimap = UIMap(
            screen_size=(1920, 1080),
            elements=[
                UIElement(
                    id="btn1",
                    role="push button",
                    name="Save",
                    bounds=Bounds(x=100, y=100, width=50, height=30),
                    state=set(),
                )
            ],
        )
        plan = brain.reason(uimap, "Click Save", [])
        assert isinstance(plan, ActionPlan)
        assert len(plan.actions) == 1
        assert plan.actions[0].type == "click"

    def test_explain_failure_returns_none(self):
        brain = StubBrain()
        result = brain.explain_failure(None, None, "error")
        assert result is None
