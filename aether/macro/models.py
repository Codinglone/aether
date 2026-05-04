from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ElementSelector(BaseModel):
    role: Optional[str] = None
    name: Optional[str] = None
    name_contains: Optional[str] = None
    index: Optional[int] = None


class Intent(BaseModel):
    action_type: str
    target: ElementSelector
    params: dict[str, Any]


class Macro(BaseModel):
    name: str
    intents: list[Intent]
