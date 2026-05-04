# Aether-Native: System Design Specification

**Version:** 1.0
**Date:** 2026-05-04
**Status:** Draft — Pending review
**Objective:** Build a cross-platform, native-first computer-use agent that outperforms cloud-based vision models by leveraging OS-level accessibility APIs and local inference.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture](#2-architecture)
3. [Component Design](#3-component-design)
4. [Platform Adapters](#4-platform-adapters)
5. [The RALPH Loop](#5-the-ralph-loop)
6. ["Wow" Features](#6-wow-features)
7. [Testing & Evaluation Framework](#7-testing--evaluation-framework)
8. [Open-Core Model](#8-open-core-model)
9. [Tech Stack](#9-tech-stack)
10. [Folder Structure](#10-folder-structure)
11. [Implementation Phases](#11-implementation-phases)
12. [MVP Acceptance Criteria](#12-mvp-acceptance-criteria)
13. [Appendix](#13-appendix)

---

## 1. Executive Summary

Aether-Native is a **local-first, cross-platform computer-use agent** for macOS, Windows, and Linux. Unlike cloud-based agents (Claude Computer Use, Perplexity) that send screenshots to remote VLMs, Aether-Native reads the OS accessibility tree directly via native APIs (AX on macOS, UIA on Windows, AT-SPI2 on Linux). This yields:

- **Sub-second latency** vs 3–6 seconds for cloud vision models
- **Pixel-perfect accuracy** vs coordinate drift from visual inference
- **Zero cloud dependency** — runs entirely on-device
- **Privacy by design** — no screen data leaves the machine

The project ships under a **FOSS-first, open-core model**: the core agent is AGPL-3.0, with commercial tiers for cloud LLM fallback, multi-agent orchestration, and enterprise features.

**Ship-fast mindset:** Phase 0 (MVP) targets a working Linux agent in 2 weeks. macOS and Windows adapters follow sequentially. Every feature is either in the MVP or defined as an architecture stub with a locked interface.

---

## 2. Architecture

### 2.1 High-Level Diagram

```
User Task (CLI / GUI / Voice)
            │
            ▼
┌─────────────────────────────────────────────┐
│          RALPH Loop (Python 3.11+)          │
│  Reason → Plan → Act → Observe → Learn     │
│         Verify → Progress → History         │
└─────────────────────────────────────────────┘
            │
    ┌───────┴───────┐
    ▼               ▼
┌─────────┐   ┌─────────────┐
│  Brain  │   │   Memory    │
│  (LLM)  │   │ knowledge   │
└─────────┘   └─────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│        Platform Adapter (Factory)           │
│   ┌─────────┐ ┌───────────┐ ┌─────────┐   │
│   │  macOS  │ │  Windows  │ │  Linux  │   │
│   │   AX    │ │   UIA     │ │ AT-SPI2 │   │
│   └─────────┘ └───────────┘ └─────────┘   │
└─────────────────────────────────────────────┘
```

### 2.2 Design Principles

1. **One language:** Python 3.11+ everywhere. No Rust/Go/C++ in Phase 0. This maximizes LLM maintainability and iteration speed.
2. **Platform-native APIs:** Each OS uses its first-class accessibility API. No lowest-common-denominator wrappers.
3. **Interface-locked adapters:** All platform adapters implement the same abstract base class. The core loop never branches on OS.
4. **Deterministic testing:** A mock adapter simulates any OS from JSON fixtures. Tests run headless in CI.
5. **Architecture stubs for future features:** "Wow" features A and C are defined with interfaces but not implemented in Phase 0.

### 2.3 API Layer (FastAPI Backbone)

All control surfaces — CLI, web dashboard, and third-party integrations — communicate with the agent via a **local FastAPI application**. This decouples the RALPH loop from its consumers and provides a standardized async interface.

**Phase 0 scope:** The FastAPI app is an architecture stub with a minimal `/health` endpoint and `/task` POST endpoint. The CLI talks directly to the RALPH loop in-process to avoid complexity. Phase 1 promotes the CLI to an HTTP client.

**Future endpoints:**
- `POST /task` — Submit a natural language task
- `GET /task/{id}` — Query task status and progress
- `GET /state` — Stream real-time UI state (WebSocket)
- `POST /macro/record` — Start/stop macro recording
- `POST /macro/play` — Replay a saved macro
- `GET /overlay` — Stream Ghost Overlay events (WebSocket)
- `POST /voice/command` — Submit voice command (Phase 2)

**Why FastAPI:**
- Native async/await fits the RALPH loop's concurrent perception + action model
- Automatic OpenAPI docs for integration developers
- WebSocket support for real-time overlay and state streaming
- Minimal boilerplate — an LLM can scaffold CRUD endpoints in minutes

---

## 3. Component Design

### 3.1 Core Loop (`aether/core/loop.py`)

The RALPH loop is a state machine with the following states:

```
IDLE → REASONING → PLANNING → EXECUTING → VERIFYING → LEARNING → IDLE
```

**Transitions:**
- `IDLE → REASONING`: User submits a task.
- `REASONING → PLANNING`: Perception captures UI state; Brain analyzes.
- `PLANNING → EXECUTING`: Brain outputs `ActionPlan`.
- `EXECUTING → VERIFYING`: Actions dispatched; perception re-captures.
- `VERIFYING → LEARNING`: Verification compares before/after states.
- `LEARNING → IDLE`: Memory updated; task marked done or retry triggered.

**Error transitions:**
- Any state → `ABORTED`: Fatal error (app crash, LLM unreachable, safety violation).
- VERIFYING → PLANNING: Verification failed; retry with learned context.

### 3.2 Perception (`aether/perception/`)

**Responsibility:** Convert the native accessibility tree into a platform-agnostic `UIMap`.

**Interface:**
```python
class PerceptionAdapter(ABC):
    @abstractmethod
    def capture(self) -> UIMap: ...
    
    @abstractmethod
    def get_active_window(self) -> Optional[UIElement]: ...
    
    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]: ...
    
    @abstractmethod
    def find_element(self, role: str, name: str) -> Optional[UIElement]: ...
```

**Output format:** `UIMap` (Pydantic model)
```python
class UIElement(BaseModel):
    id: str                    # Unique per-session ID
    role: str                  # "push button", "text", "menu item", etc.
    name: str                  # Accessible name (e.g., "Save")
    description: Optional[str] # Accessible description
    bounds: Bounds             # x, y, width, height
    state: Set[str]            # "focused", "checked", "sensitive", etc.
    children: List["UIElement"] # Nested structure
    parent_id: Optional[str]

class UIMap(BaseModel):
    timestamp: datetime
    screen_size: Tuple[int, int]
    elements: List[UIElement]
    active_window: Optional[UIElement]
    focused_element: Optional[UIElement]
```

**Markdown serialization:**
The `UIMap` is compressed to a markdown snippet for the LLM prompt:
```markdown
[1] Window: "LibreOffice Writer" (0,0,1200,800)
  [2] MenuBar: 
    [3] MenuItem: "File" (10,30,40,20)
    [4] MenuItem: "Edit" (55,30,40,20)
  [5] ToolBar: 
    [6] PushButton: "Save" (x:100, y:60, w:30, h:30)
  [7] Text: "Document body..." (x:10, y:100, w:1180, h:690)
```

**Screenshot fallback:**
If the accessibility tree is empty (e.g., a game or custom-drawn UI), the perception layer falls back to `mss` for a screenshot. The LLM is informed that visual mode is active and receives the image as base64.

### 3.3 Brain (`aether/core/brain.py`)

**Responsibility:** Interface with the local LLM to generate structured action plans.

**Interface:**
```python
class Brain(ABC):
    @abstractmethod
    def reason(self, state: UIMap, task: str, history: List[ActionRecord]) -> ActionPlan: ...
    
    @abstractmethod
    def explain_failure(self, state: UIMap, failed_action: Action, error: str) -> Optional[ActionPlan]: ...
```

**Implementation:**
- **Backend:** `llama-cpp-python` with Qwen2.5-VL-7B-Q4_K_M
- **Context window:** 32K tokens (enough for long UI trees + history)
- **Structured output:** Enforced via `instructor` library + Pydantic schema
- **Prompt template:** `prompts/planner.j2` (Jinja2, versioned, no dynamic construction)

**Prompt structure:**
```jinja2
You are a desktop automation agent. Your goal: {{ task }}

Current UI state:
{{ ui_markdown }}

Previous actions (last 5):
{{ history }}

Available actions:
- click(element_id)
- type(text, element_id)
- hotkey(mods, key)
- shell(command, timeout)
- wait(seconds)

Rules:
1. Prefer keyboard navigation when possible (more reliable than coordinates).
2. If an element is not visible, scroll or navigate to it first.
3. Never execute destructive commands (rm -rf, sudo, etc.).
4. Verify state changes after each action.

Respond with a JSON ActionPlan.
```

**ActionPlan schema:**
```python
class Action(BaseModel):
    type: Literal["click", "type", "hotkey", "shell", "wait", "scroll"]
    params: Dict[str, Any]
    reason: str                      # Why this action was chosen
    expected_change: str             # What state change validates success

class ActionPlan(BaseModel):
    task_summary: str
    actions: List[Action]
    contingency: Optional[Action]    # Fallback if first action fails
```

### 3.4 Action (`aether/action/`)

**Responsibility:** Execute physical input events and shell commands.

**Interface:**
```python
class ActionAdapter(ABC):
    @abstractmethod
    def click(self, x: int, y: int) -> None: ...
    
    @abstractmethod
    def type_text(self, text: str) -> None: ...
    
    @abstractmethod
    def hotkey(self, modifiers: List[str], key: str) -> None: ...
    
    @abstractmethod
    def scroll(self, x: int, y: int, delta: int) -> None: ...
```

**Safety layer:**
All actions pass through a `SafetyChecker` before execution:
```python
class SafetyChecker:
    SHELL_BLACKLIST = {"rm", "sudo", "mkfs", "dd", ">", "|"}
    MAX_CLICK_X = 7680  # 8K monitor
    MAX_CLICK_Y = 4320
    MAX_TYPE_LENGTH = 10000
    MAX_SHELL_TIMEOUT = 60
    
    def check(self, action: Action) -> Tuple[bool, Optional[str]]:
        # Returns (is_safe, error_message)
```

### 3.5 Memory (`aether/core/memory.py`)

**Short-term memory (in-session):**
```python
class SessionMemory:
    history: deque[ActionRecord]      # Last 50 actions
    state_history: deque[UIMap]       # Last 20 UI states
    failed_attempts: Dict[str, int]   # Track retries per action type
```

**Long-term memory (persistent):**
- `knowledge.md` — Human-editable markdown file of UI quirks:
  ```markdown
  ## LibreOffice Writer
  - The "Save" button does not always fire AT-SPI state-changed events.
    Workaround: Use Ctrl+S hotkey instead.
  
  ## Firefox
  - Tab close buttons have role="push button" but no accessible name.
    Use index-based clicking for tabs.
  ```
- `progress.json` — Machine-readable task progress:
  ```json
  {
    "current_task": "Export PDF",
    "completed_steps": ["Open File menu", "Click Export"],
    "pending_steps": ["Enter filename", "Click Save"],
    "start_time": "2026-05-04T10:00:00Z"
  }
  ```

### 3.6 Verification (`aether/core/verify.py`)

**Responsibility:** Confirm that an action produced the expected state change.

**Strategies:**
1. **Tree diff:** Compare `UIMap` before and after. Did the expected element appear/disappear/change state?
2. **Focus tracking:** Did the focused element change as expected?
3. **Window tracking:** Did the active window change?
4. **Screenshot diff (fallback):** If tree diff is inconclusive, compare screenshots with OpenCV `absdiff`.

**Interface:**
```python
class Verifier:
    def verify(self, before: UIMap, after: UIMap, action: Action) -> VerificationResult:
        ...

class VerificationResult(BaseModel):
    success: bool
    confidence: float              # 0.0–1.0
    matched_strategy: str
    details: Optional[str]
```

---

## 4. Platform Adapters

All adapters implement the same `PerceptionAdapter` and `ActionAdapter` interfaces.

### 4.1 Linux (`aether/perception/linux.py`, `aether/action/linux.py`)

**Perception:** `pyatspi2`
- Connect to `org.a11y.Bus` via D-Bus
- Recursively walk the `Accessible` tree
- Filter: `state_set.contains(pyatspi.STATE_SHOWING)`

**Action:** Priority order:
1. `ydotool` (Wayland, modern, but requires root or uinput access)
2. `pynput` (universal fallback, works on X11 and some Wayland setups)
3. `python-xlib` (X11 only, precise)

**Target environment:** Fedora 43 / GNOME / Wayland (primary), Ubuntu / X11 (secondary)

### 4.2 macOS (`aether/perception/macos.py`, `aether/action/macos.py`)

**Perception:** `ApplicationServices` framework via `pyobjc`
- `AXUIElementCreateSystemWide()`
- `AXUIElementCopyAttributeValue(..., kAXFocusedUIElementAttribute, ...)`
- Walk children via `kAXChildrenAttribute`

**Action:** `Quartz` framework via `pyobjc`
- `CGEventCreateMouseEvent(..., kCGEventLeftMouseDown, ...)`
- `CGEventPost(kCGHIDEventTap, event)`

**Permissions:** Requires user to grant "Accessibility" permissions in System Preferences.

### 4.3 Windows (`aether/perception/windows.py`, `aether/action/windows.py`)

**Perception:** `uiautomation` (pure Python, PyPI)
- `uiautomation.GetRootControl()`
- Walk tree via `GetChildren()`
- Filter by `ControlTypeName` and `Name`

**Action:** `ctypes.windll.user32.SendInput`
- `INPUT` struct for mouse/keyboard
- `MOUSEINPUT` / `KEYBDINPUT` unions

**Note:** `uiautomation` is a mature, pure-Python library. No COM interop complexity.

### 4.4 Mock Adapter (`tests/harness.py`)

For deterministic testing, the mock adapter simulates any platform from JSON fixtures:
```python
class MockAdapter(PerceptionAdapter, ActionAdapter):
    def __init__(self, fixture_path: str):
        self.fixture = json.load(open(fixture_path))
        self.state_index = 0
        self.executed_actions: List[Action] = []
    
    def capture(self) -> UIMap:
        return UIMap.from_dict(self.fixture["states"][self.state_index])
    
    def click(self, x: int, y: int):
        self.executed_actions.append(Action(type="click", params={"x": x, "y": y}))
        self._advance_state()
```

---

## 5. The RALPH Loop

**RALPH** = Reasoning, Action, Learning, Progress, History

### 5.1 Pseudocode

```python
class RalphLoop:
    def __init__(self, perception, brain, action, memory, verifier):
        self.perception = perception
        self.brain = brain
        self.action = action
        self.memory = memory
        self.verifier = verifier
        self.state = LoopState.IDLE
    
    async def run(self, task: str) -> TaskResult:
        self.state = LoopState.REASONING
        max_retries = 3
        
        for attempt in range(max_retries):
            # REASON: Capture current state
            ui_map = self.perception.capture()
            
            # PLAN: Ask brain for action plan
            plan = self.brain.reason(
                state=ui_map,
                task=task,
                history=list(self.memory.history)
            )
            
            if not plan.actions:
                return TaskResult(status="failed", reason="No actions generated")
            
            # ACT: Execute each action
            for action in plan.actions:
                self.state = LoopState.EXECUTING
                
                # Safety check
                is_safe, error = SafetyChecker().check(action)
                if not is_safe:
                    return TaskResult(status="aborted", reason=error)
                
                # Execute
                self._execute(action)
                self.memory.history.append(ActionRecord(action=action, timestamp=now()))
                
                # VERIFY: Confirm state changed
                self.state = LoopState.VERIFYING
                new_ui_map = self.perception.capture()
                result = self.verifier.verify(ui_map, new_ui_map, action)
                
                if not result.success:
                    # LEARN: Log failure and retry
                    self.state = LoopState.LEARNING
                    self.memory.failed_attempts[action.type] += 1
                    self.brain.explain_failure(new_ui_map, action, result.details)
                    break  # Retry from REASONING
                
                ui_map = new_ui_map  # Update baseline for next action
            
            else:
                # All actions succeeded — task complete
                self.state = LoopState.IDLE
                self.memory.update_progress(task, done=True)
                return TaskResult(status="success", actions_taken=len(self.memory.history))
        
        return TaskResult(status="failed", reason=f"Max retries ({max_retries}) exceeded")
```

### 5.2 Latency Budget (MVP Target: <5s per action)

| Step | Budget | Notes |
|------|--------|-------|
| Perception (AT-SPI scrape) | 50–200ms | Tree walk + serialization |
| LLM inference (Qwen 7B Q4) | 500ms–2s | Depends on prompt length |
| Action execution | 10–100ms | Native input event |
| Verification | 50–200ms | Second tree scrape + diff |
| **Total per action** | **<3s typical, <5s worst case** | |

**Phase 1 optimization target:** <1s per action via model quantization (Q4→Q3) and prompt caching.

---

## 6. "Wow" Features

### 6.1 Feature A: Ghost Overlay (Architecture Stub)

**Description:** A semi-transparent HUD overlaid on the desktop that visualizes the live accessibility tree in real-time. Every interactive element gets a labeled bounding box with its semantic role and name. When the agent is running, it highlights the element it's about to interact with.

**Why it wows:** No other agent exposes its perception layer. This demystifies AI decision-making and doubles as a debugging tool.

**Phase 0 scope:** Architecture stub only.
- Interface defined: `GhostOverlay(ABC)` with `show(uimap)`, `highlight(element_id)`, `hide()`
- Implementation deferred to Phase 1
- No GUI code in Phase 0

**Future implementation:**
- Qt or GTK overlay window with `Qt::WindowTransparentForInput` or `gdk_window_set_pass_through`
- Render bounding boxes via `QPainter` / `cairo`
- Subscribe to RALPH loop events to highlight "next action"

### 6.2 Feature B: Self-Healing Macros (Phase 0)

**Description:** Record a workflow by intent, not coordinates. The agent saves semantic actions ("click the button named 'Export as PDF'") rather than hardcoded (x, y) positions. When replaying, it dynamically resolves the element by its accessible name and role. If the UI updates and the button moves, the macro still works.

**Why it wows:** Solves the #1 pain point in RPA/UI automation. Shareable across OSes (same semantic names). Survives app updates.

**Phase 0 implementation:**
```python
class MacroRecorder:
    def start_recording(self): ...
    def stop_recording(self) -> Macro: ...
    
class Macro:
    name: str
    intents: List[Intent]          # Semantic actions
    
class Intent(BaseModel):
    action_type: str               # "click", "type", etc.
    target: ElementSelector        # Semantic selector, not coordinates
    params: Dict[str, Any]
    
class ElementSelector(BaseModel):
    role: Optional[str]
    name: Optional[str]
    name_contains: Optional[str]
    index: Optional[int]           # "3rd button named 'Close'"
    near: Optional[ElementSelector] # Spatial: "near the 'File' menu"
```

**Replay logic:**
```python
class MacroPlayer:
    def play(self, macro: Macro):
        for intent in macro.intents:
            element = self.perception.find_element(intent.target)
            if not element:
                # Self-healing: fuzzy match by role or partial name
                element = self.perception.fuzzy_find(intent.target)
            self.action.execute(intent.action_type, element, intent.params)
```

**Acceptance criteria:**
- Record a macro in LibreOffice Writer (open File → Export as PDF → Save)
- Change LibreOffice theme/window size
- Replay macro successfully without modification

### 6.3 Feature C: Accessibility Superpower / Voice Control (Architecture Stub)

**Description:** Local voice control for any desktop application via Whisper.cpp + RALPH loop. Users speak natural language commands; the agent translates them into precise accessibility actions. Because we use native APIs, we can control apps that have no scripting support.

**Why it wows:** First open-source voice control for arbitrary desktop apps. Massive accessibility impact for disabled users. Demonstrates the latency advantage (0.5s local vs 4s cloud).

**Phase 0 scope:** Architecture stub only.
- Interface defined: `VoiceInterface(ABC)` with `listen()`, `transcribe(audio) → str`, `dispatch(command: str)`
- `dispatch()` reuses the existing RALPH loop with `task=transcribed_text`
- No audio pipeline in Phase 0

**Future implementation:**
- Whisper.cpp (GGUF, local) for STT
- Optional TTS feedback via `espeak-ng` or `pyttsx3`
- Wake word detection via `porcupine` or `openwakeword`

---

## 7. Testing & Evaluation Framework

### 7.1 Philosophy

- **TDD for everything.** Every component starts with a failing test.
- **Deterministic fixtures.** No flaky UI tests. Mock adapter runs from JSON.
- **Cross-platform from day one.** macOS/Windows tests use fixtures even if adapters are stubs.

### 7.2 Test Categories

**Unit tests** (`tests/test_core/`):
- `test_loop.py` — State machine transitions, retry logic, abort conditions
- `test_brain.py` — Prompt rendering, JSON schema validation, error handling
- `test_verify.py` — Tree diff, screenshot diff, confidence scoring
- `test_memory.py` — History pruning, knowledge.md parsing, progress.json updates
- `test_safety.py` — Blacklist matching, bounds checking, timeout enforcement

**Adapter tests** (`tests/test_linux.py`, `test_macos.py`, `test_windows.py`):
- Run against mock fixtures (deterministic, headless)
- Optional: Run against real desktop (manual, marked `@pytest.mark.integration`)

**Integration tests** (`tests/test_integration.py`):
- End-to-end scenarios using mock adapter + full RALPH loop
- Example: "Open calculator, compute 2+2, verify result is 4"

**Regression tests** (`tests/regression/`):
- One fixture per reported bug
- Must fail before fix, pass after fix

### 7.3 Fixture Format

```json
{
  "name": "Calculator: 2 + 2",
  "platform": "linux",
  "app": "gnome-calculator",
  "initial_state": {
    "elements": [
      {"id": "win1", "role": "frame", "name": "Calculator", "bounds": {"x":0,"y":0,"w":300,"h":400}},
      {"id": "btn2", "role": "push button", "name": "2", "bounds": {"x":50,"y":200,"w":50,"h":50}, "parent_id": "win1"},
      {"id": "btn_plus", "role": "push button", "name": "+", "bounds": {"x":150,"y":200,"w":50,"h":50}, "parent_id": "win1"},
      {"id": "btn_eq", "role": "push button", "name": "=", "bounds": {"x":200,"y":200,"w":50,"h":50}, "parent_id": "win1"},
      {"id": "display", "role": "text", "name": "0", "bounds": {"x":10,"y":50,"w":280,"h":40}, "parent_id": "win1"}
    ]
  },
  "task": "Calculate 2 + 2",
  "expected_actions": [
    {"type": "click", "params": {"x":75, "y":225}},
    {"type": "click", "params": {"x":175, "y":225}},
    {"type": "click", "params": {"x":75, "y":225}},
    {"type": "click", "params": {"x":225, "y":225}}
  ],
  "transitions": [
    {"after_action": 0, "element_id": "display", "new_name": "2"},
    {"after_action": 1, "element_id": "display", "new_name": "2"},
    {"after_action": 2, "element_id": "display", "new_name": "2"},
    {"after_action": 3, "element_id": "display", "new_name": "4"}
  ],
  "success_condition": {
    "element_id": "display",
    "name_equals": "4"
  }
}
```

### 7.4 Evaluation Metrics

**ALR Score (Action-Latency-Reliability):**
```
ALR = (Success Rate × 100) / Average Latency (seconds)
```

**MVP targets:**
| Metric | Target | Measurement |
|--------|--------|-------------|
| Success rate (5 basic workflows) | >80% | 10 runs each |
| Average latency per action | <5s | Median of 100 actions |
| Macro replay success after UI change | >90% | 10 layout variations |
| Test coverage | >80% | `pytest --cov` |

**Phase 1 targets:**
| Metric | Target |
|--------|--------|
| Success rate | >95% |
| Average latency per action | <1s |
| Cross-platform workflow success | >90% on all 3 OSes |

---

## 8. Open-Core Model

| Tier | License | What’s Included |
|------|---------|-----------------|
| **Core** | AGPL-3.0 | All platform adapters, RALPH loop, local LLM, test harness, Ghost Overlay (Phase 1), Self-Healing Macros, Voice Control stub |
| **Open-Core** | Commercial | Cloud LLM fallback (Claude/OpenAI API), multi-agent orchestration, web dashboard, analytics |
| **Enterprise** | Commercial | On-prem deployment, SSO/SAML, audit logging, custom model fine-tuning, priority support |

**Phase 0 builds only the Core tier.** Open-Core interfaces are defined as stubs (e.g., `CloudBrainAdapter(ABC)`) but not implemented.

---

## 9. Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.11+ | LLM-friendly, fast iteration, huge ecosystem |
| **Package Manager** | `uv` | Modern, fast lockfile, reproducible builds |
| **Project Config** | `pyproject.toml` (PEP 621) | Standard, tool-agnostic |
| **CLI** | `typer` | Type-safe, auto-generated help, trivial to extend |
| **Settings** | `pydantic-settings` | Type-safe env vars, validation |
| **LLM Runtime** | `llama-cpp-python` | Local GGUF, no network, one `pip install` |
| **Model** | Qwen2.5-VL-7B-Q4_K_M | Best open VLM for tool use, fits in 8GB VRAM |
| **Structured Output** | `instructor` + Pydantic | Forces valid JSON, type-safe |
| **Linux Perception** | `pyatspi2` | Mature, well-documented |
| **macOS Perception** | `pyobjc-framework-ApplicationServices` | Native AX API |
| **Windows Perception** | `uiautomation` | Pure Python, no COM complexity |
| **Input Injection** | Platform-native (see §4) | Accuracy over convenience |
| **Screenshot** | `mss` | Cross-platform, fast, no deps |
| **Testing** | `pytest` + `pytest-asyncio` | Universal, LLM knows it |
| **Coverage** | `pytest-cov` | Standard |
| **Linting** | `ruff` | Fast, replaces flake8/black/isort |
| **Type Checking** | `mypy` | Catches bugs early |
| **API Framework** | `fastapi` + `uvicorn` | Async, auto-docs, WebSocket support |
| **Voice STT (Phase 2)** | `whisper.cpp` (GGUF) | Local, fast, no cloud |
| **Overlay (Phase 1)** | `PyQt6` or `PyGObject` | Mature, transparent window support |

---

## 10. Folder Structure

```
aether/
├── aether/
│   ├── __init__.py
│   ├── cli.py                   # Typer CLI entrypoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── loop.py              # RALPH loop orchestrator
│   │   ├── brain.py             # LLM connector
│   │   ├── memory.py            # knowledge.md + progress.json
│   │   ├── verify.py            # State verification
│   │   ├── safety.py            # Action safety checker
│   │   └── models.py            # Pydantic models (UIMap, ActionPlan, etc.)
│   ├── perception/
│   │   ├── __init__.py          # Factory: detect OS, return adapter
│   │   ├── base.py              # PerceptionAdapter ABC
│   │   ├── linux.py             # AT-SPI2
│   │   ├── macos.py             # AXUIElement
│   │   ├── windows.py           # UIA
│   │   └── screenshot.py        # mss fallback
│   ├── action/
│   │   ├── __init__.py          # Factory: detect OS, return adapter
│   │   ├── base.py              # ActionAdapter ABC
│   │   ├── linux.py             # ydotool / pynput
│   │   ├── macos.py             # Quartz Events
│   │   └── windows.py           # SendInput
│   ├── macro/
│   │   ├── __init__.py
│   │   ├── recorder.py          # MacroRecorder
│   │   ├── player.py            # MacroPlayer (self-healing)
│   │   └── models.py            # Macro, Intent, ElementSelector
│   ├── overlay/
│   │   ├── __init__.py
│   │   └── base.py              # GhostOverlay ABC (stub)
│   ├── voice/
│   │   ├── __init__.py
│   │   └── base.py              # VoiceInterface ABC (stub)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py               # FastAPI application factory
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── task.py          # POST /task, GET /task/{id}
│   │   │   ├── macro.py         # POST /macro/record, POST /macro/play
│   │   │   ├── state.py         # GET /state (WebSocket)
│   │   │   └── voice.py         # POST /voice/command (stub)
│   │   └── dependencies.py      # RALPH loop injection
│   └── prompts/
│       └── planner.j2           # Jinja2 prompt template
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures (mock adapter)
│   ├── harness.py               # MockAdapter + fixture loader
│   ├── fixtures/
│   │   ├── calculator_linux.json
│   │   ├── terminal_linux.json
│   │   ├── filemanager_linux.json
│   │   ├── texteditor_linux.json
│   │   ├── browser_linux.json
│   │   └── calculator_macos.json   # Stub for future adapter
│   ├── test_core/
│   │   ├── test_loop.py
│   │   ├── test_brain.py
│   │   ├── test_verify.py
│   │   ├── test_memory.py
│   │   └── test_safety.py
│   ├── test_linux.py
│   ├── test_macos.py
│   ├── test_windows.py
│   ├── test_integration.py
│   ├── test_macro.py
│   └── regression/
│       └── issue_001_calculator_click_miss.json
├── knowledge.md                 # Long-term UI behavior memory
├── progress.json                # Task progress tracking
├── pyproject.toml
├── README.md
└── CONTRIBUTING.md
```

---

## 11. Implementation Phases

### Phase 0: MVP — Linux Agent (Weeks 1–2)

**Goal:** Prove the loop works end-to-end on Linux.

**Deliverables:**
- [ ] `PerceptionAdapter` + `ActionAdapter` for Linux (AT-SPI2 + pynput)
- [ ] `Brain` with local Qwen2.5-VL-7B via `llama-cpp-python`
- [ ] `RalphLoop` with REASON → PLAN → ACT → VERIFY → LEARN
- [ ] `SafetyChecker` with command blacklist
- [ ] `MacroRecorder` + `MacroPlayer` (Self-Healing Macros)
- [ ] FastAPI stub with `/health` and `/task` endpoints (architecture only)
- [ ] Mock adapter + 5 basic workflow fixtures
- [ ] All tests passing in CI
- [ ] CLI: `aether run "open calculator and compute 2+2"`

**Non-goals:** macOS/Windows adapters, Ghost Overlay, Voice Control, cloud LLM fallback, dashboard UI.

### Phase 1: Cross-Platform + Polish (Weeks 3–6)

**Goal:** macOS and Windows adapters. Ghost Overlay.

**Week 3–4:** macOS adapter (AXUIElement + Quartz)
**Week 5–6:** Windows adapter (UIA + SendInput)

**Deliverables:**
- [ ] macOS and Windows `PerceptionAdapter` + `ActionAdapter`
- [ ] Cross-platform fixture set (same workflows, different OS trees)
- [ ] Ghost Overlay implementation (Qt/GTK)
- [ ] ALR score >90% on all 3 platforms
- [ ] End-to-end latency <1s per action

### Phase 2: SOTA Features (Month 2+)

**Goal:** Match/beat cloud agents on reliability and features.

**Deliverables:**
- [ ] Voice Control (Whisper.cpp + RALPH loop)
- [ ] Vision fallback (screenshot + VLM when AT-SPI fails)
- [ ] Cloud LLM bridge (OpenAI/Claude API for complex reasoning)
- [ ] Multi-agent orchestration (agent spawns sub-agents for sub-tasks)
- [ ] Web dashboard for macro management and session replay
- [ ] Enterprise tier (SSO, audit logging, on-prem)

---

## 12. MVP Acceptance Criteria

### 12.1 Functional

- [ ] **FR1:** Can scrape AT-SPI tree from a real GTK/Qt app and print compact markdown.
- [ ] **FR2:** Can execute `click`, `type`, `hotkey`, `shell` on real Linux desktop.
- [ ] **FR3:** Can complete 5/5 basic workflows on real desktop:
  1. Open calculator, compute 2+2, verify display shows 4
  2. Open terminal, run `echo hello`, verify output
  3. Open file manager, create new folder named "test"
  4. Open text editor, type "Hello World", save as `/tmp/test.txt`
  5. Open browser, navigate to `example.com`, verify title
- [ ] **FR4:** Self-healing macro: record "export PDF" in LibreOffice, change window size, replay successfully.
- [ ] **FR5:** Safety checker rejects `sudo`, `rm -rf`, and out-of-bounds clicks.

### 12.2 Performance

- [ ] **PR1:** End-to-end latency per action <5s (median over 100 actions).
- [ ] **PR2:** AT-SPI tree scrape <200ms for a typical app window (≤100 elements).
- [ ] **PR3:** LLM inference <2s for a 2K-token prompt.

### 12.3 Quality

- [ ] **QR1:** Test coverage >80% (`pytest --cov`).
- [ ] **QR2:** All unit + integration tests pass in CI (headless, no real desktop).
- [ ] **QR3:** No `mypy` errors on strict mode.
- [ ] **QR4:** No `ruff` errors.

### 12.4 Documentation

- [ ] **DR1:** `README.md` with install, quickstart, and architecture overview.
- [ ] **DR2:** `CONTRIBUTING.md` with TDD workflow and fixture format.
- [ ] **DR3:** Inline docstrings on all public classes and methods.

---

## 13. Appendix

### 13.1 Glossary

| Term | Definition |
|------|------------|
| **AT-SPI2** | Assistive Technology Service Provider Interface — Linux accessibility bus |
| **AX** | macOS Accessibility API (AXUIElement) |
| **UIA** | Microsoft UI Automation — Windows accessibility API |
| **RALPH** | Reasoning, Action, Learning, Progress, History |
| **UIMap** | Platform-agnostic representation of the UI accessibility tree |
| **GGUF** | llama.cpp model format (quantized) |
| **Ghost Overlay** | Semi-transparent HUD showing live accessibility tree |
| **Self-Healing Macro** | Recorded workflow that resolves elements by name, not coordinates |
| **FastAPI** | Async Python web framework for API, dashboard, and WebSocket endpoints |

### 13.2 Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| AT-SPI2 unavailable (app not exposing tree) | High | Medium | Screenshot fallback + VLM mode |
| Wayland input injection blocked | High | Medium | Document permissions; fallback to `ydotool` daemon |
| macOS permissions dialog blocks automation | High | High | Document setup; provide `tccutil` helper script |
| Qwen2.5-VL too slow on CPU | Medium | Low | Recommend GPU; document min specs; support cloud fallback stub |
| LLM generates invalid JSON | Medium | Medium | `instructor` library with retries; Pydantic validation |

### 13.3 Related Work

| Project | Approach | Aether-Native Differentiator |
|---------|----------|------------------------------|
| **Claude Computer Use** | Cloud VLM + pixel coordinates | Local, native APIs, sub-second latency |
| **Perplexity** | Cloud VLM + screenshot | Same as above |
| **Open Interpreter** | LLM generates code | Not agentic; no loop/verification |
| **UI.Vision** | Pixel-based RPA | Not self-healing; brittle to UI changes |
| **Selenium / Playwright** | Browser-only | Aether controls the entire desktop |

---

**End of Specification**

*This document is a living spec. Changes must be reviewed and versioned. The canonical source is `docs/superpowers/specs/YYYY-MM-DD-aether-native-design.md`.*
