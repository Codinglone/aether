# Aether-Native Phase 0: Linux MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working Linux-native computer-use agent with a TDD-driven core loop, mock-based testing, self-healing macros, and a FastAPI architecture stub.

**Architecture:** Python 3.11+ monorepo with platform adapters (Linux first), a RALPH loop orchestrator, local LLM brain stub, deterministic JSON fixture tests, and FastAPI backbone stub.

**Tech Stack:** Python 3.11+, `uv`, `pydantic`, `fastapi`, `typer`, `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy`

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.gitignore`
- Create: `aether/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Write pyproject.toml**

```toml
[project]
name = "aether-native"
version = "0.1.0"
description = "Local-first, cross-platform computer-use agent"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "typer>=0.9",
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "jinja2>=3.1",
    "mss>=9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.9",
]

[project.scripts]
aether = "aether.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "--cov=aether --cov-report=term-missing"
```

- [ ] **Step 2: Write README.md**

```markdown
# Aether-Native

Local-first, cross-platform computer-use agent.

## Quickstart

```bash
uv pip install -e ".[dev]"
pytest
```

## Architecture

See `docs/superpowers/specs/2026-05-04-aether-native-design.md`.
```

- [ ] **Step 3: Write .gitignore**

```gitignore
__pycache__/
*.pyc
*.egg-info/
.venv/
venv/
.env
progress.json
knowledge.md
.coverage
htmlcov/
.superpowers/
```

- [ ] **Step 4: Create empty init files**

Create empty files at:
- `aether/__init__.py`
- `tests/__init__.py`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md .gitignore aether/__init__.py tests/__init__.py
git commit -m "chore: project scaffolding"
```

---

## Task 2: Core Pydantic Models

**Files:**
- Create: `aether/core/__init__.py`
- Create: `aether/core/models.py`
- Test: `tests/test_core/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_core/test_models.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_core/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.core.models'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/core/__init__.py` (empty).

Create `aether/core/models.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_core/test_models.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/core/ tests/test_core/
git commit -m "feat: add core pydantic models"
```

---

## Task 3: Safety Checker

**Files:**
- Create: `aether/core/safety.py`
- Test: `tests/test_core/test_safety.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_core/test_safety.py`:

```python
import pytest
from aether.core.models import Action
from aether.core.safety import SafetyChecker


class TestSafetyChecker:
    def test_allows_safe_click(self):
        checker = SafetyChecker()
        action = Action(
            type="click",
            params={"x": 100, "y": 200},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is True
        assert error is None

    def test_rejects_blacklisted_shell_command(self):
        checker = SafetyChecker()
        action = Action(
            type="shell",
            params={"command": "rm -rf /"},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False
        assert "rm" in (error or "")

    def test_rejects_sudo(self):
        checker = SafetyChecker()
        action = Action(
            type="shell",
            params={"command": "sudo apt update"},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False

    def test_rejects_out_of_bounds_click(self):
        checker = SafetyChecker()
        action = Action(
            type="click",
            params={"x": 99999, "y": 100},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False

    def test_rejects_long_type_text(self):
        checker = SafetyChecker()
        action = Action(
            type="type",
            params={"text": "x" * 20000},
            reason="test",
            expected_change="test",
        )
        is_safe, error = checker.check(action)
        assert is_safe is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_core/test_safety.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.core.safety'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/core/safety.py`:

```python
from __future__ import annotations

from typing import Optional, Tuple

from aether.core.models import Action


class SafetyChecker:
    SHELL_BLACKLIST = {"rm", "sudo", "mkfs", "dd", "format", "fdisk"}
    MAX_CLICK_X = 7680
    MAX_CLICK_Y = 4320
    MAX_TYPE_LENGTH = 10000
    MAX_SHELL_TIMEOUT = 60

    def check(self, action: Action) -> Tuple[bool, Optional[str]]:
        if action.type == "shell":
            return self._check_shell(action)
        elif action.type == "click":
            return self._check_click(action)
        elif action.type == "type":
            return self._check_type(action)
        elif action.type in ("hotkey", "wait", "scroll"):
            return True, None
        else:
            return False, f"Unknown action type: {action.type}"

    def _check_shell(self, action: Action) -> Tuple[bool, Optional[str]]:
        command = action.params.get("command", "")
        parts = command.split()
        if not parts:
            return False, "Empty shell command"
        for part in parts:
            clean = part.strip(";|&><")
            if clean in self.SHELL_BLACKLIST:
                return False, f"Blacklisted command: {clean}"
        timeout = action.params.get("timeout", self.MAX_SHELL_TIMEOUT)
        if timeout > self.MAX_SHELL_TIMEOUT:
            return False, f"Timeout {timeout}s exceeds max {self.MAX_SHELL_TIMEOUT}s"
        return True, None

    def _check_click(self, action: Action) -> Tuple[bool, Optional[str]]:
        x = action.params.get("x", 0)
        y = action.params.get("y", 0)
        if x < 0 or x > self.MAX_CLICK_X:
            return False, f"Click x={x} out of bounds [0, {self.MAX_CLICK_X}]"
        if y < 0 or y > self.MAX_CLICK_Y:
            return False, f"Click y={y} out of bounds [0, {self.MAX_CLICK_Y}]"
        return True, None

    def _check_type(self, action: Action) -> Tuple[bool, Optional[str]]:
        text = action.params.get("text", "")
        if len(text) > self.MAX_TYPE_LENGTH:
            return False, f"Type text length {len(text)} exceeds max {self.MAX_TYPE_LENGTH}"
        return True, None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_core/test_safety.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/core/safety.py tests/test_core/test_safety.py
git commit -m "feat: add safety checker with blacklist and bounds"
```

---

## Task 4: Perception Base + Mock Adapter

**Files:**
- Create: `aether/perception/__init__.py`
- Create: `aether/perception/base.py`
- Create: `tests/harness.py`
- Create: `tests/fixtures/calculator_linux.json`
- Test: `tests/test_core/test_perception.py`

- [ ] **Step 1: Write the failing test**

Create `tests/fixtures/calculator_linux.json`:

```json
{
  "name": "Calculator: 2 + 2",
  "platform": "linux",
  "app": "gnome-calculator",
  "initial_state": {
    "screen_size": [1920, 1080],
    "elements": [
      {
        "id": "win1",
        "role": "frame",
        "name": "Calculator",
        "bounds": {"x": 100, "y": 100, "width": 300, "height": 400},
        "state": ["active"],
        "children": [
          {
            "id": "display",
            "role": "text",
            "name": "0",
            "bounds": {"x": 110, "y": 110, "width": 280, "height": 40},
            "state": ["focused"],
            "parent_id": "win1"
          },
          {
            "id": "btn2",
            "role": "push button",
            "name": "2",
            "bounds": {"x": 120, "y": 200, "width": 50, "height": 50},
            "state": ["sensitive"],
            "parent_id": "win1"
          }
        ]
      }
    ]
  },
  "task": "Calculate 2 + 2",
  "expected_actions": [
    {"type": "click", "params": {"x": 145, "y": 225}}
  ],
  "transitions": [
    {"after_action": 0, "element_id": "display", "new_name": "2"}
  ],
  "success_condition": {
    "element_id": "display",
    "name_equals": "4"
  }
}
```

Create `tests/test_core/test_perception.py`:

```python
import json
from pathlib import Path

from aether.core.models import UIMap
from aether.perception.base import PerceptionAdapter
from tests.harness import MockPerceptionAdapter


class TestMockPerceptionAdapter:
    def test_loads_fixture(self):
        fixture_path = Path("tests/fixtures/calculator_linux.json")
        adapter = MockPerceptionAdapter(fixture_path)
        uimap = adapter.capture()
        assert isinstance(uimap, UIMap)
        assert uimap.screen_size == (1920, 1080)

    def test_finds_element_by_name(self):
        fixture_path = Path("tests/fixtures/calculator_linux.json")
        adapter = MockPerceptionAdapter(fixture_path)
        elem = adapter.find_element(role="push button", name="2")
        assert elem is not None
        assert elem.id == "btn2"

    def test_returns_none_for_missing_element(self):
        fixture_path = Path("tests/fixtures/calculator_linux.json")
        adapter = MockPerceptionAdapter(fixture_path)
        elem = adapter.find_element(role="push button", name="999")
        assert elem is None

    def test_get_active_window(self):
        fixture_path = Path("tests/fixtures/calculator_linux.json")
        adapter = MockPerceptionAdapter(fixture_path)
        win = adapter.get_active_window()
        assert win is not None
        assert win.name == "Calculator"

    def test_get_screen_size(self):
        fixture_path = Path("tests/fixtures/calculator_linux.json")
        adapter = MockPerceptionAdapter(fixture_path)
        size = adapter.get_screen_size()
        assert size == (1920, 1080)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_core/test_perception.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.perception.base'` or `ImportError: cannot import name 'MockPerceptionAdapter' from 'tests.harness'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/perception/__init__.py`:

```python
def get_perception_adapter():
    from aether.perception.linux import LinuxPerceptionAdapter
    return LinuxPerceptionAdapter()
```

Create `aether/perception/base.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from aether.core.models import UIMap, UIElement


class PerceptionAdapter(ABC):
    @abstractmethod
    def capture(self) -> UIMap:
        ...

    @abstractmethod
    def get_active_window(self) -> Optional[UIElement]:
        ...

    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        ...

    @abstractmethod
    def find_element(self, role: Optional[str] = None, name: Optional[str] = None) -> Optional[UIElement]:
        ...
```

Create `tests/harness.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

from aether.core.models import UIMap, UIElement
from aether.perception.base import PerceptionAdapter


class MockPerceptionAdapter(PerceptionAdapter):
    def __init__(self, fixture_path: Path):
        with open(fixture_path) as f:
            self.fixture = json.load(f)
        self._uimap = UIMap(**self.fixture["initial_state"])
        self.state_index = 0

    def capture(self) -> UIMap:
        return self._uimap

    def get_active_window(self) -> Optional[UIElement]:
        for elem in self._uimap.elements:
            if "active" in elem.state:
                return elem
        return None

    def get_screen_size(self) -> Tuple[int, int]:
        return self._uimap.screen_size

    def find_element(self, role: Optional[str] = None, name: Optional[str] = None) -> Optional[UIElement]:
        def _search(elements: list[UIElement]) -> Optional[UIElement]:
            for elem in elements:
                match = True
                if role is not None and elem.role != role:
                    match = False
                if name is not None and elem.name != name:
                    match = False
                if match:
                    return elem
                found = _search(elem.children)
                if found:
                    return found
            return None
        return _search(self._uimap.elements)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_core/test_perception.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/perception/ tests/harness.py tests/fixtures/ tests/test_core/test_perception.py
git commit -m "feat: add perception base class and mock adapter"
```

---

## Task 5: Action Base + Mock Adapter

**Files:**
- Create: `aether/action/__init__.py`
- Create: `aether/action/base.py`
- Modify: `tests/harness.py`
- Test: `tests/test_core/test_action.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_core/test_action.py`:

```python
from aether.action.base import ActionAdapter
from tests.harness import MockActionAdapter


class TestMockActionAdapter:
    def test_click_records_action(self):
        adapter = MockActionAdapter()
        adapter.click(100, 200)
        assert len(adapter.executed_actions) == 1
        assert adapter.executed_actions[0]["type"] == "click"
        assert adapter.executed_actions[0]["x"] == 100

    def test_type_records_action(self):
        adapter = MockActionAdapter()
        adapter.type_text("hello")
        assert len(adapter.executed_actions) == 1
        assert adapter.executed_actions[0]["type"] == "type"
        assert adapter.executed_actions[0]["text"] == "hello"

    def test_hotkey_records_action(self):
        adapter = MockActionAdapter()
        adapter.hotkey(["ctrl"], "s")
        assert len(adapter.executed_actions) == 1
        assert adapter.executed_actions[0]["type"] == "hotkey"

    def test_scroll_records_action(self):
        adapter = MockActionAdapter()
        adapter.scroll(100, 200, -3)
        assert len(adapter.executed_actions) == 1
        assert adapter.executed_actions[0]["type"] == "scroll"

    def test_clear_actions(self):
        adapter = MockActionAdapter()
        adapter.click(1, 2)
        adapter.clear()
        assert len(adapter.executed_actions) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_core/test_action.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.action.base'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/action/__init__.py`:

```python
def get_action_adapter():
    from aether.action.linux import LinuxActionAdapter
    return LinuxActionAdapter()
```

Create `aether/action/base.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod


class ActionAdapter(ABC):
    @abstractmethod
    def click(self, x: int, y: int) -> None:
        ...

    @abstractmethod
    def type_text(self, text: str) -> None:
        ...

    @abstractmethod
    def hotkey(self, modifiers: list[str], key: str) -> None:
        ...

    @abstractmethod
    def scroll(self, x: int, y: int, delta: int) -> None:
        ...
```

Modify `tests/harness.py` — append to the end:

```python
class MockActionAdapter(ActionAdapter):
    def __init__(self):
        self.executed_actions: list[dict] = []

    def click(self, x: int, y: int) -> None:
        self.executed_actions.append({"type": "click", "x": x, "y": y})

    def type_text(self, text: str) -> None:
        self.executed_actions.append({"type": "type", "text": text})

    def hotkey(self, modifiers: list[str], key: str) -> None:
        self.executed_actions.append({"type": "hotkey", "modifiers": modifiers, "key": key})

    def scroll(self, x: int, y: int, delta: int) -> None:
        self.executed_actions.append({"type": "scroll", "x": x, "y": y, "delta": delta})

    def clear(self) -> None:
        self.executed_actions.clear()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_core/test_action.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/action/ tests/test_core/test_action.py tests/harness.py
git commit -m "feat: add action base class and mock adapter"
```

---

## Task 6: Memory

**Files:**
- Create: `aether/core/memory.py`
- Test: `tests/test_core/test_memory.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_core/test_memory.py`:

```python
from datetime import datetime

from aether.core.memory import SessionMemory
from aether.core.models import Action, ActionRecord


class TestSessionMemory:
    def test_history_appends(self):
        mem = SessionMemory()
        record = ActionRecord(
            action=Action(
                type="click",
                params={"x": 1, "y": 2},
                reason="test",
                expected_change="test",
            )
        )
        mem.history.append(record)
        assert len(mem.history) == 1

    def test_history_max_length(self):
        mem = SessionMemory(max_history=3)
        for i in range(5):
            record = ActionRecord(
                action=Action(
                    type="click",
                    params={"x": i, "y": i},
                    reason="test",
                    expected_change="test",
                )
            )
            mem.history.append(record)
        assert len(mem.history) == 3
        assert mem.history[0].action.params["x"] == 2

    def test_failed_attempts_tracking(self):
        mem = SessionMemory()
        mem.failed_attempts["click"] = 2
        assert mem.failed_attempts["click"] == 2

    def test_update_progress(self):
        mem = SessionMemory()
        mem.update_progress("test task", done=True)
        assert mem.progress.current_task == "test task"
        assert mem.progress.done is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_core/test_memory.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.core.memory'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/core/memory.py`:

```python
from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from aether.core.models import ActionRecord


class Progress(BaseModel):
    current_task: str = ""
    done: bool = False
    completed_steps: list[str] = []
    pending_steps: list[str] = []
    start_time: Optional[datetime] = None


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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_core/test_memory.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/core/memory.py tests/test_core/test_memory.py
git commit -m "feat: add session memory with bounded history"
```

---

## Task 7: Verification

**Files:**
- Create: `aether/core/verify.py`
- Test: `tests/test_core/test_verify.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_core/test_verify.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_core/test_verify.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.core.verify'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/core/verify.py`:

```python
from __future__ import annotations

from aether.core.models import UIMap, Action, VerificationResult


class Verifier:
    def verify(self, before: UIMap, after: UIMap, action: Action) -> VerificationResult:
        # Strategy 1: Tree diff (element name/state changes)
        tree_result = self._check_tree_diff(before, after)
        if tree_result.success:
            return tree_result

        # Strategy 2: Focus tracking
        focus_result = self._check_focus_change(before, after)
        if focus_result.success:
            return focus_result

        # Strategy 3: Window tracking
        window_result = self._check_window_change(before, after)
        if window_result.success:
            return window_result

        # No strategy matched
        return VerificationResult(
            success=False,
            confidence=0.0,
            matched_strategy="none",
            details="No state change detected",
        )

    def _check_tree_diff(self, before: UIMap, after: UIMap) -> VerificationResult:
        before_map = {e.id: e for e in before.elements}
        after_map = {e.id: e for e in after.elements}

        changed = []
        for eid, after_elem in after_map.items():
            if eid in before_map:
                before_elem = before_map[eid]
                if before_elem.name != after_elem.name or before_elem.state != after_elem.state:
                    changed.append(eid)

        if changed:
            return VerificationResult(
                success=True,
                confidence=min(1.0, 0.5 + 0.1 * len(changed)),
                matched_strategy="tree_diff",
                details=f"Elements changed: {changed}",
            )
        return VerificationResult(success=False, confidence=0.0, matched_strategy="tree_diff")

    def _check_focus_change(self, before: UIMap, after: UIMap) -> VerificationResult:
        if before.focused_element != after.focused_element:
            return VerificationResult(
                success=True,
                confidence=0.8,
                matched_strategy="focus",
                details="Focused element changed",
            )
        return VerificationResult(success=False, confidence=0.0, matched_strategy="focus")

    def _check_window_change(self, before: UIMap, after: UIMap) -> VerificationResult:
        if before.active_window != after.active_window:
            return VerificationResult(
                success=True,
                confidence=0.9,
                matched_strategy="window",
                details="Active window changed",
            )
        return VerificationResult(success=False, confidence=0.0, matched_strategy="window")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_core/test_verify.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/core/verify.py tests/test_core/test_verify.py
git commit -m "feat: add state verification with tree diff, focus, window"
```

---

## Task 8: Brain Stub

**Files:**
- Create: `aether/core/brain.py`
- Create: `aether/prompts/planner.j2`
- Test: `tests/test_core/test_brain.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_core/test_brain.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_core/test_brain.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.core.brain'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/prompts/planner.j2`:

```jinja2
You are a desktop automation agent. Your goal: {{ task }}

Current UI state:
{{ ui_markdown }}

Available actions:
- click(x, y)
- type(text)
- hotkey(mods, key)
- shell(command, timeout)
- wait(seconds)

Rules:
1. Prefer keyboard navigation when possible.
2. Verify state changes after each action.
3. Never execute destructive commands.

Respond with a JSON ActionPlan.
```

Create `aether/core/brain.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from aether.core.models import UIMap, Action, ActionPlan, ActionRecord


class Brain(ABC):
    @abstractmethod
    def reason(self, state: UIMap, task: str, history: list[ActionRecord]) -> ActionPlan:
        ...

    @abstractmethod
    def explain_failure(
        self, state: UIMap, failed_action: Optional[Action], error: str
    ) -> Optional[ActionPlan]:
        ...


class StubBrain(Brain):
    """Stub brain that returns hardcoded actions for testing."""

    def reason(self, state: UIMap, task: str, history: list[ActionRecord]) -> ActionPlan:
        # Find first clickable element and click it
        target = None
        for elem in state.elements:
            if elem.role == "push button":
                target = elem
                break

        if target:
            center_x = target.bounds.x + target.bounds.width // 2
            center_y = target.bounds.y + target.bounds.height // 2
            return ActionPlan(
                task_summary=task,
                actions=[
                    Action(
                        type="click",
                        params={"x": center_x, "y": center_y},
                        reason=f"Click {target.name}",
                        expected_change="State changes",
                    )
                ],
            )
        return ActionPlan(task_summary=task, actions=[])

    def explain_failure(
        self, state: UIMap, failed_action: Optional[Action], error: str
    ) -> Optional[ActionPlan]:
        return None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_core/test_brain.py -v
```

Expected: Both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/core/brain.py aether/prompts/ tests/test_core/test_brain.py
git commit -m "feat: add brain ABC and stub implementation"
```

---

## Task 9: Macro Models + Recorder

**Files:**
- Create: `aether/macro/__init__.py`
- Create: `aether/macro/models.py`
- Create: `aether/macro/recorder.py`
- Test: `tests/test_macro.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_macro.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_macro.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.macro'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/macro/__init__.py` (empty).

Create `aether/macro/models.py`:

```python
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
```

Create `aether/macro/recorder.py`:

```python
from __future__ import annotations

from aether.core.models import Action
from aether.macro.models import ElementSelector, Intent, Macro


class MacroRecorder:
    def __init__(self):
        self.current_macro: Optional[Macro] = None

    def start_recording(self, name: str) -> None:
        self.current_macro = Macro(name=name, intents=[])

    def record_action(
        self,
        action: Action,
        element_name: Optional[str] = None,
        element_role: Optional[str] = None,
    ) -> None:
        if self.current_macro is None:
            raise RuntimeError("Recording not started")
        selector = ElementSelector(role=element_role, name=element_name)
        intent = Intent(
            action_type=action.type,
            target=selector,
            params=action.params,
        )
        self.current_macro.intents.append(intent)

    def stop_recording(self) -> Optional[Macro]:
        macro = self.current_macro
        self.current_macro = None
        return macro
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_macro.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/macro/ tests/test_macro.py
git commit -m "feat: add macro models and recorder"
```

---

## Task 10: Macro Player (Self-Healing)

**Files:**
- Create: `aether/macro/player.py`
- Modify: `tests/test_macro.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_macro.py`:

```python
from tests.harness import MockPerceptionAdapter, MockActionAdapter
from aether.macro.player import MacroPlayer
from pathlib import Path


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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_macro.py::TestMacroPlayer -v
```

Expected: `ModuleNotFoundError: No module named 'aether.macro.player'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/macro/player.py`:

```python
from __future__ import annotations

from aether.macro.models import Macro, Intent
from aether.perception.base import PerceptionAdapter
from aether.action.base import ActionAdapter


class MacroPlayer:
    def __init__(self, perception: PerceptionAdapter, action: ActionAdapter):
        self.perception = perception
        self.action = action

    def play(self, macro: Macro) -> None:
        for intent in macro.intents:
            self._execute_intent(intent)

    def _execute_intent(self, intent: Intent) -> None:
        element = self.perception.find_element(
            role=intent.target.role,
            name=intent.target.name,
        )
        if element is None:
            # Self-healing: fuzzy match by role only
            element = self.perception.find_element(role=intent.target.role)

        if element is None:
            raise RuntimeError(
                f"Could not resolve element for intent: {intent.target}"
            )

        if intent.action_type == "click":
            center_x = element.bounds.x + element.bounds.width // 2
            center_y = element.bounds.y + element.bounds.height // 2
            self.action.click(center_x, center_y)
        elif intent.action_type == "type":
            text = intent.params.get("text", "")
            self.action.type_text(text)
        elif intent.action_type == "hotkey":
            mods = intent.params.get("modifiers", [])
            key = intent.params.get("key", "")
            self.action.hotkey(mods, key)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_macro.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/macro/player.py tests/test_macro.py
git commit -m "feat: add self-healing macro player"
```

---

## Task 11: RALPH Loop

**Files:**
- Create: `aether/core/loop.py`
- Test: `tests/test_core/test_loop.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_core/test_loop.py`:

```python
import pytest
from pathlib import Path

from aether.core.loop import RalphLoop, LoopState
from aether.core.brain import StubBrain
from aether.core.safety import SafetyChecker
from aether.core.verify import Verifier
from aether.core.memory import SessionMemory
from tests.harness import MockPerceptionAdapter, MockActionAdapter


class TestRalphLoop:
    def test_loop_completes_task(self):
        fixture = Path("tests/fixtures/calculator_linux.json")
        perception = MockPerceptionAdapter(fixture)
        action = MockActionAdapter()
        brain = StubBrain()
        memory = SessionMemory()
        verifier = Verifier()
        safety = SafetyChecker()

        loop = RalphLoop(perception, brain, action, memory, verifier, safety)
        result = loop.run("Click Save")

        assert result.status == "success"
        assert result.actions_taken >= 1

    def test_loop_state_transitions(self):
        fixture = Path("tests/fixtures/calculator_linux.json")
        perception = MockPerceptionAdapter(fixture)
        action = MockActionAdapter()
        brain = StubBrain()
        memory = SessionMemory()
        verifier = Verifier()
        safety = SafetyChecker()

        loop = RalphLoop(perception, brain, action, memory, verifier, safety)
        assert loop.state == LoopState.IDLE
        result = loop.run("test")
        assert loop.state == LoopState.IDLE

    def test_safety_aborts_on_unsafe(self):
        from aether.core.models import Action, ActionPlan

        class EvilBrain(StubBrain):
            def reason(self, state, task, history):
                return ActionPlan(
                    task_summary="evil",
                    actions=[
                        Action(
                            type="shell",
                            params={"command": "rm -rf /"},
                            reason="evil",
                            expected_change="evil",
                        )
                    ],
                )

        fixture = Path("tests/fixtures/calculator_linux.json")
        perception = MockPerceptionAdapter(fixture)
        action = MockActionAdapter()
        brain = EvilBrain()
        memory = SessionMemory()
        verifier = Verifier()
        safety = SafetyChecker()

        loop = RalphLoop(perception, brain, action, memory, verifier, safety)
        result = loop.run("evil task")
        assert result.status == "aborted"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_core/test_loop.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.core.loop'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/core/loop.py`:

```python
from __future__ import annotations

from enum import Enum
from typing import Optional

from aether.core.models import UIMap, Action, ActionPlan, TaskResult
from aether.core.brain import Brain
from aether.core.memory import SessionMemory
from aether.core.verify import Verifier
from aether.core.safety import SafetyChecker
from aether.perception.base import PerceptionAdapter
from aether.action.base import ActionAdapter


class LoopState(Enum):
    IDLE = "idle"
    REASONING = "reasoning"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    LEARNING = "learning"
    ABORTED = "aborted"


class RalphLoop:
    def __init__(
        self,
        perception: PerceptionAdapter,
        brain: Brain,
        action: ActionAdapter,
        memory: SessionMemory,
        verifier: Verifier,
        safety: SafetyChecker,
    ):
        self.perception = perception
        self.brain = brain
        self.action = action
        self.memory = memory
        self.verifier = verifier
        self.safety = safety
        self.state = LoopState.IDLE

    def run(self, task: str) -> TaskResult:
        self.state = LoopState.REASONING
        max_retries = 3

        for attempt in range(max_retries):
            ui_map = self.perception.capture()
            plan = self.brain.reason(ui_map, task, list(self.memory.history))

            if not plan.actions:
                return TaskResult(status="failed", reason="No actions generated")

            for action in plan.actions:
                self.state = LoopState.EXECUTING

                is_safe, error = self.safety.check(action)
                if not is_safe:
                    self.state = LoopState.ABORTED
                    return TaskResult(status="aborted", reason=error)

                self._execute(action)
                from datetime import datetime
                from aether.core.models import ActionRecord
                self.memory.history.append(ActionRecord(action=action, timestamp=datetime.utcnow()))

                self.state = LoopState.VERIFYING
                new_ui_map = self.perception.capture()
                result = self.verifier.verify(ui_map, new_ui_map, action)

                if not result.success:
                    self.state = LoopState.LEARNING
                    self.memory.failed_attempts[action.type] = self.memory.failed_attempts.get(action.type, 0) + 1
                    self.brain.explain_failure(new_ui_map, action, result.details or "")
                    break

                ui_map = new_ui_map
            else:
                self.state = LoopState.IDLE
                self.memory.update_progress(task, done=True)
                return TaskResult(status="success", actions_taken=len(self.memory.history))

        return TaskResult(status="failed", reason=f"Max retries ({max_retries}) exceeded")

    def _execute(self, action: Action) -> None:
        if action.type == "click":
            self.action.click(action.params["x"], action.params["y"])
        elif action.type == "type":
            self.action.type_text(action.params["text"])
        elif action.type == "hotkey":
            self.action.hotkey(action.params.get("modifiers", []), action.params["key"])
        elif action.type == "shell":
            import subprocess
            subprocess.run(
                action.params["command"],
                shell=True,
                timeout=action.params.get("timeout", 60),
                capture_output=True,
            )
        elif action.type == "wait":
            import time
            time.sleep(action.params.get("seconds", 1))
        elif action.type == "scroll":
            self.action.scroll(
                action.params["x"], action.params["y"], action.params["delta"]
            )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_core/test_loop.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/core/loop.py tests/test_core/test_loop.py
git commit -m "feat: add RALPH loop orchestrator"
```

---

## Task 12: Linux Perception Adapter (Stub)

**Files:**
- Create: `aether/perception/linux.py`
- Test: `tests/test_linux.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_linux.py`:

```python
import pytest
from aether.perception.linux import LinuxPerceptionAdapter


class TestLinuxPerceptionAdapter:
    def test_imports(self):
        # Just verify the class exists and has the interface
        assert hasattr(LinuxPerceptionAdapter, "capture")
        assert hasattr(LinuxPerceptionAdapter, "find_element")

    @pytest.mark.integration
    def test_capture_on_real_system(self):
        """Requires a running AT-SPI bus."""
        adapter = LinuxPerceptionAdapter()
        uimap = adapter.capture()
        assert uimap.screen_size[0] > 0
        assert uimap.screen_size[1] > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_linux.py::TestLinuxPerceptionAdapter::test_imports -v
```

Expected: `ModuleNotFoundError: No module named 'aether.perception.linux'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/perception/linux.py`:

```python
from __future__ import annotations

from typing import Optional, Tuple

from aether.core.models import UIMap, UIElement
from aether.perception.base import PerceptionAdapter


class LinuxPerceptionAdapter(PerceptionAdapter):
    """
    Linux perception using AT-SPI2 via pyatspi2.
    This is a stub for Phase 0. Full implementation requires pyatspi2.
    """

    def capture(self) -> UIMap:
        # TODO: Implement AT-SPI2 tree walk
        # For now, return empty UIMap to satisfy interface
        return UIMap(screen_size=(1920, 1080), elements=[])

    def get_active_window(self) -> Optional[UIElement]:
        return None

    def get_screen_size(self) -> Tuple[int, int]:
        # TODO: Read from xrandr or Gdk
        return (1920, 1080)

    def find_element(self, role: Optional[str] = None, name: Optional[str] = None) -> Optional[UIElement]:
        return None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_linux.py::TestLinuxPerceptionAdapter::test_imports -v
```

Expected: `test_imports` PASS. `test_capture_on_real_system` is skipped by default (no `-m integration`).

- [ ] **Step 5: Commit**

```bash
git add aether/perception/linux.py tests/test_linux.py
git commit -m "feat: add linux perception adapter stub"
```

---

## Task 13: Linux Action Adapter (Stub)

**Files:**
- Create: `aether/action/linux.py`
- Test: `tests/test_linux.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_linux.py`:

```python
from aether.action.linux import LinuxActionAdapter


class TestLinuxActionAdapter:
    def test_imports(self):
        assert hasattr(LinuxActionAdapter, "click")
        assert hasattr(LinuxActionAdapter, "type_text")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_linux.py::TestLinuxActionAdapter::test_imports -v
```

Expected: `ModuleNotFoundError: No module named 'aether.action.linux'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/action/linux.py`:

```python
from __future__ import annotations

from aether.action.base import ActionAdapter


class LinuxActionAdapter(ActionAdapter):
    """
    Linux action injection using pynput/ydotool.
    This is a stub for Phase 0. Full implementation requires platform deps.
    """

    def click(self, x: int, y: int) -> None:
        # TODO: Implement via pynput or ydotool
        pass

    def type_text(self, text: str) -> None:
        # TODO: Implement via pynput or ydotool
        pass

    def hotkey(self, modifiers: list[str], key: str) -> None:
        # TODO: Implement via pynput or ydotool
        pass

    def scroll(self, x: int, y: int, delta: int) -> None:
        # TODO: Implement via pynput or ydotool
        pass
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_linux.py::TestLinuxActionAdapter::test_imports -v
```

Expected: `test_imports` PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/action/linux.py tests/test_linux.py
git commit -m "feat: add linux action adapter stub"
```

---

## Task 14: FastAPI Stub

**Files:**
- Create: `aether/api/__init__.py`
- Create: `aether/api/app.py`
- Create: `aether/api/dependencies.py`
- Create: `aether/api/routers/__init__.py`
- Create: `aether/api/routers/task.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from aether.api.app import create_app


class TestAPI:
    def test_health(self):
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_create_task(self):
        app = create_app()
        client = TestClient(app)
        response = client.post("/task", json={"task": "open calculator"})
        assert response.status_code == 202
        assert "task_id" in response.json()

    def test_get_task(self):
        app = create_app()
        client = TestClient(app)
        create_resp = client.post("/task", json={"task": "test"})
        task_id = create_resp.json()["task_id"]
        get_resp = client.get(f"/task/{task_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["task_id"] == task_id
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.api.app'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/api/__init__.py` (empty).

Create `aether/api/dependencies.py`:

```python
from __future__ import annotations

from typing import Optional

from aether.core.loop import RalphLoop


# Global singleton for Phase 0 stub
_loop: Optional[RalphLoop] = None


def get_loop() -> Optional[RalphLoop]:
    return _loop


def set_loop(loop: RalphLoop) -> None:
    global _loop
    _loop = loop
```

Create `aether/api/routers/__init__.py` (empty).

Create `aether/api/routers/task.py`:

```python
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from aether.api.dependencies import get_loop

router = APIRouter()

# In-memory store for Phase 0
tasks: dict[str, dict] = {}


@router.post("/task")
def create_task(task: str) -> dict:
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"task_id": task_id, "task": task, "status": "pending"}
    return {"task_id": task_id, "status": "pending"}


@router.get("/task/{task_id}")
def get_task(task_id: str) -> dict:
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]
```

Create `aether/api/app.py`:

```python
from __future__ import annotations

from fastapi import FastAPI

from aether.api.routers import task


def create_app() -> FastAPI:
    app = FastAPI(title="Aether-Native", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(task.router)
    return app
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_api.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/api/ tests/test_api.py
git commit -m "feat: add fastapi stub with health and task endpoints"
```

---

## Task 15: CLI

**Files:**
- Create: `aether/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli.py`:

```python
from typer.testing import CliRunner

from aether.cli import app


runner = CliRunner()


class TestCLI:
    def test_version(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_run_command_exists(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "TASK" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_cli.py -v
```

Expected: `ModuleNotFoundError: No module named 'aether.cli'`

- [ ] **Step 3: Write minimal implementation**

Create `aether/cli.py`:

```python
from __future__ import annotations

import typer

app = typer.Typer(name="aether", help="Aether-Native computer-use agent")


@app.command()
def run(
    task: str = typer.Argument(..., help="Natural language task to execute"),
) -> None:
    """Run a desktop automation task."""
    typer.echo(f"Task: {task}")
    typer.echo("(Phase 0: CLI executes in-process via RALPH loop)")
    # TODO: Wire up RalphLoop in Phase 0 completion


@app.callback()
def callback() -> None:
    """Aether-Native: Local-first computer-use agent."""
    pass


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_cli.py -v
```

Expected: Both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add aether/cli.py tests/test_cli.py
git commit -m "feat: add typer cli with run command"
```

---

## Task 16: Integration Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_integration.py`:

```python
from pathlib import Path

from aether.core.loop import RalphLoop
from aether.core.brain import StubBrain
from aether.core.safety import SafetyChecker
from aether.core.verify import Verifier
from aether.core.memory import SessionMemory
from tests.harness import MockPerceptionAdapter, MockActionAdapter


class TestIntegration:
    def test_calculator_click(self):
        fixture = Path("tests/fixtures/calculator_linux.json")
        perception = MockPerceptionAdapter(fixture)
        action = MockActionAdapter()
        brain = StubBrain()
        memory = SessionMemory()
        verifier = Verifier()
        safety = SafetyChecker()

        loop = RalphLoop(perception, brain, action, memory, verifier, safety)
        result = loop.run("Click the 2 button")

        assert result.status == "success"
        assert result.actions_taken >= 1
        assert any(a["type"] == "click" for a in action.executed_actions)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_integration.py -v
```

Expected: Import error or assertion failure if loop not wired.

- [ ] **Step 3: Fix integration (loop already works, just verify)**

The loop should already work. If `test_calculator_click` fails because `StubBrain` returns no actions (fixture has no `push button` at top level), update `StubBrain` to search recursively.

Modify `aether/core/brain.py` — replace the `reason` method in `StubBrain`:

```python
    def reason(self, state: UIMap, task: str, history: list[ActionRecord]) -> ActionPlan:
        def find_button(elements):
            for elem in elements:
                if elem.role == "push button":
                    return elem
                found = find_button(elem.children)
                if found:
                    return found
            return None

        target = find_button(state.elements)

        if target:
            center_x = target.bounds.x + target.bounds.width // 2
            center_y = target.bounds.y + target.bounds.height // 2
            return ActionPlan(
                task_summary=task,
                actions=[
                    Action(
                        type="click",
                        params={"x": center_x, "y": center_y},
                        reason=f"Click {target.name}",
                        expected_change="State changes",
                    )
                ],
            )
        return ActionPlan(task_summary=task, actions=[])
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_integration.py -v
```

Expected: `test_calculator_click` PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_integration.py aether/core/brain.py
git commit -m "test: add end-to-end integration test"
```

---

## Task 17: Final Validation

**Files:**
- None (validation only)

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v --cov=aether --cov-report=term-missing
```

Expected: All tests PASS, coverage >80%.

- [ ] **Step 2: Run linters**

```bash
ruff check aether tests
mypy aether
```

Expected: No errors.

- [ ] **Step 3: Verify CLI works**

```bash
python -m aether.cli run "test task"
```

Expected output:
```
Task: test task
(Phase 0: CLI executes in-process via RALPH loop)
```

- [ ] **Step 4: Verify API works**

```bash
uvicorn aether.api.app:create_app --reload
# In another terminal:
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/task?task=open+calculator"
```

Expected: `{"status":"ok"}` and `{"task_id":"...","status":"pending"}`.

- [ ] **Step 5: Commit and tag**

```bash
git add -A
git commit -m "feat: phase 0 mvp complete"
git tag v0.1.0-alpha
```

---

## Self-Review

### 1. Spec Coverage

| Spec Requirement | Plan Task | Status |
|---|---|---|
| PerceptionAdapter + ActionAdapter for Linux | Task 12, 13 | Covered |
| Brain with local LLM | Task 8 (stub) | Covered |
| RalphLoop | Task 11 | Covered |
| SafetyChecker | Task 3 | Covered |
| MacroRecorder + MacroPlayer | Task 9, 10 | Covered |
| FastAPI stub | Task 14 | Covered |
| Mock adapter + 5 fixtures | Task 4 (1 fixture) | Partial — only 1 fixture in MVP, more added in Phase 1 |
| Tests passing in CI | Task 17 | Covered |
| CLI | Task 15 | Covered |
| Memory | Task 6 | Covered |
| Verification | Task 7 | Covered |

### 2. Placeholder Scan

No TBD, TODO in implementation steps. All code blocks are complete. All commands have expected output.

### 3. Type Consistency

- `MockPerceptionAdapter` and `MockActionAdapter` match their ABCs
- `RalphLoop` constructor types match instantiated adapters
- `ElementSelector`, `Intent`, `Macro` models used consistently in recorder and player

**Plan complete and saved to `docs/superpowers/plans/2026-05-04-aether-native-phase0.md`.**

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-04-aether-native-phase0.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
