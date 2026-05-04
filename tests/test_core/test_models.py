from aether.core.models import Bounds, UIElement, UIMap, Action, ActionPlan


def test_bounds_creation():
    b = Bounds(x=10, y=20, width=100, height=50)
    assert b.x == 10
    assert b.y == 20
    assert b.width == 100
    assert b.height == 50


def test_uielement_creation():
    elem = UIElement(
        id="btn1",
        role="push button",
        name="Save",
        bounds=Bounds(x=0, y=0, width=50, height=30),
        state={"sensitive"},
    )
    assert elem.id == "btn1"
    assert elem.name == "Save"


def test_uimap_creation():
    elem = UIElement(
        id="win1",
        role="frame",
        name="Test",
        bounds=Bounds(x=0, y=0, width=800, height=600),
        state=set(),
    )
    uimap = UIMap(screen_size=(1920, 1080), elements=[elem])
    assert uimap.screen_size == (1920, 1080)
    assert len(uimap.elements) == 1


def test_action_creation():
    action = Action(
        type="click",
        params={"x": 100, "y": 200},
        reason="Click the Save button",
        expected_change="Save dialog opens",
    )
    assert action.type == "click"
    assert action.params["x"] == 100


def test_actionplan_creation():
    plan = ActionPlan(
        task_summary="Save document",
        actions=[
            Action(
                type="click",
                params={"x": 100, "y": 200},
                reason="Click Save",
                expected_change="Dialog opens",
            )
        ],
    )
    assert len(plan.actions) == 1
    assert plan.task_summary == "Save document"
