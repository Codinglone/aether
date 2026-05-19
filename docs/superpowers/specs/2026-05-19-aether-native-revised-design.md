# Aether-Native: Revised Design Specification

**Version:** 2.0
**Date:** 2026-05-19
**Status:** Approved
**Objective:** Make the existing Python/Linux prototype a robust, end-to-end working agent. Abandon the premature cross-platform/Rust vision. Focus on closing the RALPH loop with a real brain, persistent memory, and verified task completion.

---

## 1. Honest Assessment of Current State

### What Actually Exists (2026-05-19)
- **Language:** Python 3.11+, not Rust.
- **Platform:** Linux only (AT-SPI2 + ydotool/Xlib). macOS/Windows adapters are stubs.
- **Perception:** `pyatspi2` tree walking works. Screenshot capture via ffmpeg/grim/PIL works.
- **Action:** Mouse/keyboard via `ydotool` (Wayland) and `python-xlib` (X11). Smooth animation implemented.
- **Brain:** `StubBrain` hardcodes actions. `LocalLLM` connects to Ollama but the "screenshot analysis" is text-only (feeds a file path as text to a 1B model).
- **Memory:** In-memory only. No persistence.
- **Learning:** Not implemented. `knowledge.md` and `progress.json` do not exist.
- **Tests:** 59 unit tests pass, but 0% coverage on real Linux code (`linux.py`, `hybrid.py`, `screenshot.py`, `local_llm.py`).
- **Demos:** 12 copy-paste scripts. Most are variations of "click YouTube fullscreen."

### What the Blueprint Promised vs. Reality

| Blueprint Claim | Reality |
|-----------------|---------|
| Rust 1.80+ | Python 3.14 |
| `libei` + Mutter D-Bus | `ydotool` daemon + Xlib |
| `llama.cpp` Vulkan | Ollama HTTP API |
| Qwen2.5-VL-7B | llama3.2:1B (text-only) |
| Cross-platform (macOS/Windows/Linux) | Linux only |
| Self-healing macros | Recorder exists, never used in a real task |
| Ghost Overlay | Doesn't exist |
| Voice Control | Doesn't exist |

**Decision:** Stop pretending. The Rust/cross-platform vision was a fantasy. The Python stack is not the problem. The problem is the RALPH loop is not closed.

---

## 2. Revised Architecture

### 2.1 Honest Scope

- **One OS:** Linux (Fedora/GNOME/Wayland primary, Ubuntu/X11 secondary).
- **One Language:** Python 3.11+.
- **One Goal:** A user types a natural language task. The agent completes it autonomously, verifies success, and learns from failures.

### 2.2 High-Level Diagram

```
User Task (CLI)
        |
        v
+------------------+
|   RALPH Loop     |
| (closed loop)    |
+--------+---------+
         |
    +----+----+------+--------+
    |         |      |        |
    v         v      v        v
+--------+  +-----+ +-----+ +-------+
| Hybrid |  |Local| |Linux| |Persist|
|Percept.|  |LLM  | |Action| |Memory |
+--------+  +-----+ +-----+ +-------+
    |         |      |        |
    v         v      v        v
+--------+  +-----+ +-----+ +-------+
| AT-SPI |  |Ollam| |ydoto| |knowledge|
|Primary |  |a API| |ol   | |.md    |
+--------+  +-----+ +-----+ +-------+
    |
    v
+--------+
|llava   |
|fallback|
+--------+
```

### 2.3 Design Principles

1. **Close the loop before adding platforms.** A working Linux agent is infinitely more valuable than three broken stubs.
2. **The brain must reason.** `StubBrain` is deleted. The local LLM generates action plans from UI state + task + history.
3. **Perception must be hybrid and real.** AT-SPI is primary. When it fails, `llava` (multimodal) analyzes the actual screenshot image. Never feed a file path as text.
4. **Memory must persist.** Failures and successes survive across sessions.
5. **Demos must verify.** 3 end-to-end tasks with pass/fail assertions. No more "look at the screen and see if it worked."

---

## 3. Component Design (Revised)

### 3.1 Perception: `HybridPerceptionAdapter` (Default)

**Current:** Standalone class, not wired into RALPH loop. Text-only LLM fallback.

**Target:** Default perception for all loop operations.

```python
class HybridPerceptionAdapter(PerceptionAdapter):
    def capture(self) -> UIMap:
        # 1. Try AT-SPI primary
        # 2. If empty or insufficient, capture screenshot + run llava
        # 3. Return merged UIMap with source attribution
        ...

    def find_element(self, name: str, role: Optional[str] = None) -> Optional[UIElement]:
        # 1. Search AT-SPI tree
        # 2. If not found AND llava available → vision fallback
        # 3. Return element with confidence + source metadata
        ...
```

**Vision Fallback (Real):**
- `ollama pull llava` (or `moondream`, `bakllava`)
- Encode screenshot as base64 PNG
- POST to `/api/generate` with `images` field
- Prompt: "Find the [element]. Return JSON: {found, element_name, coordinates, confidence}"
- Parse coordinates, create `UIElement` with `metadata={"source": "llava", "confidence": 0.85}`

### 3.2 Brain: `LocalLLMBrain` (Replaces `StubBrain`)

**Current:** `StubBrain` hardcodes "click the first push button."

**Target:** Uses the local LLM for actual reasoning.

```python
class LocalLLMBrain(Brain):
    def reason(self, state: UIMap, task: str, history: list[ActionRecord]) -> ActionPlan:
        # Render prompt: task + ui_markdown + history + available_actions
        # Call LLM.generate() with structured JSON output
        # Parse into ActionPlan
        # If JSON invalid → retry once with stronger system prompt
        ...

    def explain_failure(self, state: UIMap, failed_action: Action, error: str) -> Optional[ActionPlan]:
        # "The previous action failed. Here is the current state. Suggest an alternative."
        ...

    def suggest_action(self, task: str, elements: list[dict], history: list[str]) -> dict:
        # Used by demos and integration tests
        ...
```

**Prompt Template (`prompts/planner.j2`):**
```jinja2
You are a desktop automation agent running on Linux (GNOME/Wayland).

User task: {{ task }}

Current UI state (AT-SPI accessibility tree):
{{ ui_markdown }}

{{ vision_context }}

Previous actions (last {{ history|length }}):
{{ history_markdown }}

Available actions:
- click(element_id or x, y)
- type(text, element_id optional)
- hotkey(mods, key)
- shell(command, timeout)
- wait(seconds)
- scroll(x, y, delta)

Rules:
1. Prefer keyboard shortcuts when available (more reliable than coordinates).
2. If an element is not visible, scroll or tab to it first.
3. NEVER execute: rm, sudo, mkfs, dd, format, fdisk.
4. After each action, the system will verify the state changed.
5. If verification fails, you will be called again with the new state.

Respond with a JSON ActionPlan:
{
  "task_summary": "brief description",
  "actions": [
    {
      "type": "click",
      "params": {"x": 100, "y": 200},
      "reason": "why this action",
      "expected_change": "what should change in the UI"
    }
  ]
}
```

### 3.3 Memory: Persistent Session Memory

**Current:** In-memory `deque`. Lost on process exit.

**Target:** Load on init, save on every change.

```python
class SessionMemory:
    def __init__(self, data_dir: Path = Path("~/.local/share/aether")):
        self.data_dir = data_dir.expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        # Load from data_dir / "memory.json"
        ...

    def _save(self):
        # Atomic write to data_dir / "memory.json"
        ...
```

**`memory.json` schema:**
```json
{
  "history": [...],
  "failed_attempts": {"click": 3, "type": 1},
  "progress": {"current_task": "", "done": false, "completed_steps": [], "pending_steps": []},
  "knowledge": [
    {
      "app": "Brave",
      "pattern": "YouTube fullscreen",
      "action": "Press 'f' key instead of clicking fullscreen button",
      "confidence": 0.9,
      "source": "learned"
    }
  ]
}
```

### 3.4 Knowledge Store

**Current:** Doesn't exist.

**Target:** Human-readable `knowledge.md` + machine-readable `knowledge.json` (inside `memory.json`).

**`knowledge.md` format:**
```markdown
## Brave
- **Pattern:** YouTube fullscreen
- **Learned:** Press 'f' key. Clicking the fullscreen button at bottom-right is unreliable because coordinates vary with window size.
- **Confidence:** 0.9
- **Date:** 2026-05-19

## GNOME Settings
- **Pattern:** Bluetooth toggle
- **Learned:** The toggle is a "switch" role, not "push button". Use AT-SPI action interface (doAction(0)) rather than click coordinates.
- **Confidence:** 0.95
- **Date:** 2026-05-19
```

**Usage in Brain:** Before generating a plan, search knowledge for the target app. Inject relevant tips into the prompt.

### 3.5 Action: `LinuxActionAdapter` (Unchanged Interface, Better Fallbacks)

**Current:** Works. ydotool + Xlib. Smooth mouse animation.

**Minor improvements:**
- Add `focus_window_by_atspi(name)` using AT-SPI `getState().contains(STATE_ACTIVE)` + `grabFocus()`
- Better error messages when `ydotoold` is not running
- Retry on `ydotool` failure (daemon sometimes drops commands)

### 3.6 Verification: `Verifier` (Enhanced)

**Current:** Tree diff, focus tracking, window tracking.

**Addition:** Screenshot diff fallback.
- If tree diff is inconclusive (e.g., canvas changed but AT-SPI tree didn't), compare before/after screenshots with perceptual hashing.
- This is the "did the video actually go fullscreen?" check.

---

## 4. The RALPH Loop (Closed)

```python
class RalphLoop:
    def run(self, task: str) -> TaskResult:
        self.state = LoopState.REASONING
        self.memory.load_knowledge_for_task(task)  # Inject known quirks

        for attempt in range(max_retries):
            # 1. PERCEIVE
            ui_map = self.perception.capture()

            # 2. REASON
            plan = self.brain.reason(ui_map, task, list(self.memory.history))
            if not plan.actions:
                return TaskResult(status="failed", reason="No actions generated")

            for action in plan.actions:
                # 3. SAFETY
                is_safe, error = self.safety.check(action)
                if not is_safe:
                    return TaskResult(status="aborted", reason=error)

                # 4. EXECUTE
                self._execute(action)
                self.memory.record_action(action)

                # 5. VERIFY
                new_ui_map = self.perception.capture()
                result = self.verifier.verify(ui_map, new_ui_map, action)

                if not result.success:
                    # 6. LEARN
                    self.memory.record_failure(action, result.details)
                    alternative = self.brain.explain_failure(new_ui_map, action, result.details)
                    if alternative:
                        plan = alternative
                        break
                    else:
                        break  # Retry from REASONING

                ui_map = new_ui_map
            else:
                # 7. PROGRESS
                self.memory.mark_task_done(task)
                self.memory.write_knowledge(task, plan)
                return TaskResult(status="success")

        return TaskResult(status="failed", reason="Max retries exceeded")
```

---

## 5. End-to-End Verified Tasks (Replaces 12 Demos)

### Task 1: Calculator "2 + 2 = 4"
**Goal:** Open calculator, compute 2+2, verify display shows 4.
**Verification:** AT-SPI tree diff on display element.
**Why:** Proves AT-SPI primary path works end-to-end.

### Task 2: YouTube Fullscreen in Brave
**Goal:** Open Brave, navigate to a known YouTube video, make it fullscreen.
**Verification:** Screenshot diff (check for absence of window decorations) OR AT-SPI active window name change.
**Why:** Proves hybrid perception (AT-SPI for browser, vision/keyboard fallback for video player) and real brain planning.

### Task 3: Toggle Bluetooth in GNOME Settings
**Goal:** Open Settings, navigate to Bluetooth panel, toggle the switch, verify state changed.
**Verification:** AT-SPI state change on the switch element.
**Why:** Proves AT-SPI action interface (`doAction(0)`) and verification of non-text state changes.

**All tasks run as pytest integration tests.** They can be skipped with `@pytest.mark.integration` for CI.

---

## 6. Testing Strategy (Revised)

### 6.1 Test Pyramid

| Layer | What | Coverage Target |
|-------|------|-----------------|
| Unit | Models, safety, memory, verification | >90% (mock-based) |
| Integration | 3 e2e tasks against real desktop | Real desktop required |
| Regression | One fixture per known UI quirk | Automatic |

### 6.2 Coverage Reality Check

**Current:** 38% total, 0% on Linux real code.

**Target:**
- Core modules (models, safety, memory, verify, loop): >90%
- `local_llm.py`: Unit test with mocked `urllib.request`
- `screenshot.py`: Unit test with mocked `subprocess`
- `hybrid.py`: Unit test with mocked AT-SPI + mocked LLM
- `linux.py`: Integration tests only (requires real desktop)

### 6.3 CI Strategy

- **Unit tests:** Run on every commit (GitHub Actions, headless).
- **Integration tests:** Run manually or on scheduled nightly builds. Require a real Linux desktop (nested Mutter or VM).

---

## 7. Implementation Plan

### Phase A: Close the Loop (Week 1)

1. **Delete `StubBrain`.** Implement `LocalLLMBrain` with real prompt rendering and JSON parsing.
2. **Wire `HybridPerceptionAdapter` into `RalphLoop`.** Make it the default.
3. **Add `llava` vision fallback.** Real image analysis, not text guessing.
4. **Persist memory.** `SessionMemory` loads/saves `~/.local/share/aether/memory.json`.
5. **Add `KnowledgeStore`.** Writes to `knowledge.md` + `knowledge.json`.

### Phase B: Verified Tasks (Week 2)

6. **Write Task 1: Calculator e2e test.**
7. **Write Task 2: YouTube e2e test.**
8. **Write Task 3: Bluetooth e2e test.**
9. **Delete 12 old demo scripts.** Keep 1 `demo.py` as a quick sanity check.
10. **Write integration test harness.** Runs e2e tasks with pass/fail assertions.

### Phase C: Polish (Week 3)

11. **Add screenshot diff to Verifier.**
12. **Improve error handling and retry logic.**
13. **Update all documentation.** README, Blueprint, this spec.
14. **Add `aether run "task description"` CLI command.**

---

## 8. Acceptance Criteria

### Functional
- [ ] `aether run "Open calculator and compute 2+2"` succeeds and verifies display shows 4.
- [ ] `aether run "Play Big Buck Bunny on YouTube in fullscreen"` succeeds.
- [ ] `aether run "Toggle Bluetooth in Settings"` succeeds and verifies state changed.
- [ ] If AT-SPI fails, system automatically falls back to `llava` vision.
- [ ] After a successful task, `knowledge.md` contains a new entry.
- [ ] After a failed task, `memory.json` records the failure pattern.

### Performance
- [ ] AT-SPI scrape: <200ms
- [ ] LLM reasoning (1B model): <500ms
- [ ] Vision fallback (llava): <3s
- [ ] End-to-end task latency: <30s for a 5-action task

### Quality
- [ ] Unit test coverage on core modules: >90%
- [ ] All unit tests pass in CI (headless)
- [ ] All 3 integration tests pass on real desktop
- [ ] `ruff` and `mypy` clean
- [ ] No `StubBrain` or hardcoded demo coordinates

---

## 9. Tech Stack (Honest)

| Component | Technology | Why |
|-----------|------------|-----|
| Language | Python 3.11+ | Existing codebase, fast iteration |
| Package Manager | `uv` | Already in use |
| Perception (Primary) | `pyatspi2` | Works on real Linux apps |
| Perception (Fallback) | `llava` via Ollama | Actually sees screenshots |
| Screenshot | `ffmpeg` / `grim` / `PIL` | Already implemented |
| Action | `ydotool` + `python-xlib` | Already implemented |
| Brain | Ollama HTTP API (`llama3.2:1b` + `llava`) | Local, fast enough for reasoning |
| Memory | JSON on disk | Simple, inspectable |
| Knowledge | `knowledge.md` + `knowledge.json` | Human + machine readable |
| API | FastAPI stub | Already exists, expand later |
| CLI | `typer` | Already exists |
| Testing | `pytest` + `pytest-asyncio` | Already exists |

---

## 10. What Was Removed from the Blueprint

| Removed Item | Reason |
|--------------|--------|
| Rust rewrite | Python works. Rewrite would take 6 months with zero user value. |
| macOS/Windows adapters | Focus on one working OS. Ports come after product-market fit. |
| `libei` / Mutter D-Bus | `ydotool` works today. No user-facing benefit from migration. |
| `llama.cpp` Vulkan | Ollama HTTP API is simpler and sufficient for 1B-7B models. |
| Ghost Overlay | Cool, but not required for the core loop. Defer to Phase 2. |
| Voice Control | Same as above. |
| Cloud LLM fallback stub | Local models are good enough. Add cloud later if needed. |
| Self-healing macros (full feature) | Recorder exists, but no real use case proven yet. Keep code, defer polish. |
| 12 demo scripts | Replaced by 3 verified integration tests. |

---

## 11. Folder Structure (Minimal Changes)

```
aether/
├── aether/
│   ├── cli.py
│   ├── core/
│   │   ├── loop.py              # Wire in HybridPerceptionAdapter + LocalLLMBrain
│   │   ├── brain.py             # Replace StubBrain with LocalLLMBrain
│   │   ├── memory.py            # Add persistence
│   │   ├── knowledge.py         # NEW: KnowledgeStore
│   │   ├── verify.py            # Add screenshot diff fallback
│   │   ├── safety.py            # Unchanged
│   │   └── models.py            # Minor additions (metadata, source)
│   ├── perception/
│   │   ├── hybrid.py            # Wire into loop, make default
│   │   ├── screenshot.py        # Unchanged
│   │   ├── linux.py             # Minor improvements
│   │   └── base.py              # Unchanged
│   ├── action/
│   │   ├── linux.py             # Minor improvements
│   │   └── base.py              # Unchanged
│   ├── brain/                   # NEW module (was loose file)
│   │   ├── __init__.py
│   │   └── local_llm.py         # Add vision support
│   ├── macro/                   # Keep, defer polish
│   ├── api/                     # Keep as stub
│   └── prompts/
│       └── planner.j2           # Real prompt template
├── tests/
│   ├── test_core/               # Expand coverage
│   ├── test_integration.py      # 3 e2e verified tasks
│   └── fixtures/
├── knowledge.md                 # Created at runtime
├── pyproject.toml
├── README.md
└── PROGRESS.md
```

---

**End of Specification**

*This document supersedes `2026-05-04-aether-native-design.md`. The old blueprint is archived for reference but no longer authoritative.*
