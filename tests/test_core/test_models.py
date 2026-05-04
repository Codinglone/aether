from datetime import datetime, timezone

import pytest

from aether.core.models import (
    Action,
    ActionPlan,
    ActionRecord,
    Bounds,
    TaskResult,
    UIMap,
    UIElement,
    VerificationResult,
)


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


def test_uielement_defaults():
    elem = UIElement(
        id="btn1",
        role="push button",
        name="OK",
        bounds=Bounds(x=0, y=0, width=10, height=10),
    )
    assert elem.state == set()
    assert elem.children == []


def test_uielement_nested_children():
    child = UIElement(
        id="child1",
        role="push button",
        name="Child",
        bounds=Bounds(x=0, y=0, width=10, height=10),
    )
    parent = UIElement(
        id="parent1",
        role="frame",
        name="Parent",
        bounds=Bounds(x=0, y=0, width=100, height=100),
        children=[child],
    )
    assert len(parent.children) == 1
    assert parent.children[0].id == "child1"


def test_uielement_optional_fields_omitted():
    elem = UIElement(
        id="btn1",
        role="push button",
        name="OK",
        bounds=Bounds(x=0, y=0, width=10, height=10),
    )
    assert elem.description is None
    assert elem.parent_id is None


def test_verification_result_creation():
    vr = VerificationResult(
        success=True,
        confidence=0.95,
        matched_strategy="exact_text",
    )
    assert vr.success is True
    assert vr.confidence == 0.95
    assert vr.matched_strategy == "exact_text"
    assert vr.details is None


def test_verification_result_confidence_bounds():
    with pytest.raises(ValueError):
        VerificationResult(
            success=True,
            confidence=1.5,
            matched_strategy="exact_text",
        )
    with pytest.raises(ValueError):
        VerificationResult(
            success=True,
            confidence=-0.1,
            matched_strategy="exact_text",
        )


def test_action_record_creation():
    action = Action(
        type="click",
        params={"x": 100},
        reason="Click",
        expected_change="Change",
    )
    record = ActionRecord(action=action)
    assert record.action == action
    assert isinstance(record.timestamp, datetime)
    assert (datetime.now(timezone.utc) - record.timestamp).total_seconds() < 5


def test_task_result_creation():
    tr = TaskResult(status="success")
    assert tr.status == "success"
    assert tr.actions_taken == 0
    assert tr.reason is None
