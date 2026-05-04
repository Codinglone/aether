from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from aether.api.dependencies import get_loop

router = APIRouter()

# In-memory store for Phase 0
tasks: dict[str, dict] = {}


class TaskRequest(BaseModel):
    task: str


@router.post("/task", status_code=202)
def create_task(req: TaskRequest) -> dict:
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"task_id": task_id, "task": req.task, "status": "pending"}
    return {"task_id": task_id, "status": "pending"}


@router.get("/task/{task_id}")
def get_task(task_id: str) -> dict:
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]
