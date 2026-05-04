from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from aether.core.models import ActionRecord


class Progress(BaseModel):
    current_task: str = ""
    done: bool = False
    completed_steps: list[str] = []
    pending_steps: list[str] = []
    start_time: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionMemory:
    def __init__(self, max_history: int = 50, max_states: int = 20):
        self.history: deque[ActionRecord] = deque(maxlen=max_history)
        self.state_history: deque = deque(maxlen=max_states)
        self.failed_attempts: dict[str, int] = {}
        self.progress = Progress()

    def update_progress(self, task: str, done: bool = False) -> None:
        self.progress.current_task = task
        self.progress.done = done
        if done:
            self.progress.completed_steps.append(task)
