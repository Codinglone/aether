from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Set, Tuple

from pydantic import BaseModel


class Bounds(BaseModel):
    x: int
    y: int
    width: int
    height: int


class UIElement(BaseModel):
    id: str
    role: str
    name: str
    description: Optional[str] = None
    bounds: Bounds
    state: Set[str] = set()
    children: list["UIElement"] = []
    parent_id: Optional[str] = None


class UIMap(BaseModel):
    timestamp: datetime = datetime.utcnow()
    screen_size: Tuple[int, int]
    elements: list[UIElement]
    active_window: Optional[UIElement] = None
    focused_element: Optional[UIElement] = None


class Action(BaseModel):
    type: str
    params: dict[str, Any]
    reason: str
    expected_change: str


class ActionPlan(BaseModel):
    task_summary: str
    actions: list[Action]
    contingency: Optional[Action] = None


class VerificationResult(BaseModel):
    success: bool
    confidence: float
    matched_strategy: str
    details: Optional[str] = None


class ActionRecord(BaseModel):
    action: Action
    timestamp: datetime = datetime.utcnow()


class TaskResult(BaseModel):
    status: str
    actions_taken: int = 0
    reason: Optional[str] = None
