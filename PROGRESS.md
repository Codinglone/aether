# Aether-Native Progress Log

**Date:** 2026-05-19
**Session:** Design pivot — abandon Rust/cross-platform fantasy, focus on closing the RALPH loop
**Commit:** (docs update)

---

## Honest Assessment

The project had drifted into fantasy land. The blueprint described Rust, `libei`, `pipewire-rs`, cross-platform adapters, Ghost Overlay, and Voice Control. The reality was Python, `ydotool`, 12 copy-paste YouTube demos, and a `StubBrain` that hardcoded "click the first button."

**Decision:** Stop pretending. Make the Python/Linux prototype actually work.

### What Was Wrong

1. **No real brain.** `StubBrain` didn't reason; it just clicked the first push button it found.
2. **Hybrid perception not wired into the loop.** `HybridPerceptionAdapter` existed but was never used by `RalphLoop`.
3. **Vision fallback was fake.** `LocalLLM.analyze_screenshot()` fed a *file path as text* to a 1B text-only model and asked it to guess coordinates.
4. **No persistence.** Memory was in-memory only. No `knowledge.md`, no `progress.json`.
5. **0% test coverage on real code.** All tests exercised mocks. The Linux action/perception code was completely untested.
6. **12 demos, 0 verification.** Every demo ended with "look at the screen and see if it worked."

### New Design Philosophy

- **One OS:** Linux. macOS/Windows are future possibilities, not current goals.
- **One Language:** Python. Rust was a premature optimization.
- **Close the loop:** Perceive → Reason → Act → Verify → Learn. All five steps must work.
- **Verify or delete:** Every task must have a pass/fail assertion. No more manual eyeballing.

---

## New Architecture (Simplified)

```
User Task
    |
    v
+-----------+     +------------------+     +---------+
|  RALPH    |<--->| Hybrid Perception|<--->| AT-SPI  |
|  Loop     |     | (AT-SPI + llava) |     | Primary |
+-----------+     +------------------+     +---------+
    |  ^                |
    |  |                v
    |  |           +---------+
    |  |           |  llava  |
    |  |           |Fallback |
    |  |           +---------+
    |  |
    v  |
+-----------+     +---------+     +----------+
|  Local    |     |  Linux  |     | Persist  |
|  LLM      |     | Action  |     | Memory   |
|  Brain    |     |         |     |          |
+-----------+     +---------+     +----------+
```

---

## Revised Task List (Priority Order)

### Phase A: Close the Loop (Week 1) ✅ COMPLETE

- [x] **Task 1: Real prompt template (`planner.j2`)**
- [x] **Task 2: `LocalLLMBrain` replaces `StubBrain`**
  - Real prompt rendering, JSON parsing with retry, `explain_failure()`
  - Network error handling, template file error handling
- [x] **Task 3: `llava` vision fallback**
  - Base64-encoded screenshot images sent to Ollama `/api/generate`
  - Model state leak fixed (restore in `finally` block)
- [x] **Task 4: Persistent `SessionMemory`**
  - Loads/saves `~/.local/share/aether/memory.json` atomically
  - `record_action()`, `record_failure()`, `mark_task_done()`
- [x] **Task 5: `KnowledgeStore`**
  - Writes to `knowledge.md` + `knowledge.json`
  - Injects learned tips into LLM prompt
- [x] **Task 6: Wire everything into `RalphLoop`**
  - Knowledge injection before reasoning
  - Persistent memory on every action
  - Knowledge learned on successful task completion
  - 3 demo scripts using closed loop (calculator, settings, browser)

### Phase B: Verified End-to-End Tasks (Week 2) — IN PROGRESS

- [ ] **Task 7: Calculator integration test**
  - Open calculator, compute 2+2, verify display shows 4
- [ ] **Task 8: Settings integration test**
  - Open GNOME Settings, toggle Bluetooth, verify state changed
- [ ] **Task 9: Browser integration test**
  - Open Brave, navigate to example.com, verify page loaded
- [ ] **Task 10: Delete old demos**
  - Keep `demo.py` as smoke test, remove 12 copy-paste YouTube demos

### Phase C: Polish (Week 3)

- [ ] **Task 11: Screenshot diff verifier**
  - Perceptual hashing fallback when tree diff is inconclusive
- [ ] **Task 12: Improve error handling and retry logic**
  - Better messages when `ydotoold` is not running
  - "Stuck" detection (same state 3x in a row)
- [ ] **Task 13: Update all documentation**
  - Inline docstrings for all public methods
- [ ] **Task 14: CLI command `aether run "task description"`**
  - Make `run` actually execute the RALPH loop

### Phase D: Testing & Quality

- [ ] **Task 15: Unit test coverage >90% on core modules**
  - Mock `urllib.request` for `local_llm.py`
  - Mock `subprocess` for `screenshot.py`
  - Mock AT-SPI for `hybrid.py`
- [ ] **Task 16: Integration test harness**
  - Runs e2e tasks in a controlled desktop session
- [ ] **Task 17: ruff + mypy clean**
  - Fix all lint and type errors

---

## Key Decisions

1. **Python, not Rust.** The existing Python stack works. Rewriting would be 6 months of zero user value.
2. **Linux, not cross-platform.** One working OS beats three broken stubs.
3. **Ollama HTTP API over `llama-cpp-python`.** HTTP is simpler, no complex bindings, easy to mock in tests.
4. **3 verified tasks over 12 demos.** Quality over quantity. Every task must prove itself.
5. **Persistence is not optional.** An agent that forgets everything on exit is not an agent.

## What Was Fixed

- `StubBrain` deleted, `LocalLLMBrain` generates real action plans from UI state + task
- `HybridPerceptionAdapter` wired into `RalphLoop` as default perception
- `LocalLLM.analyze_screenshot_vision()` sends actual base64-encoded images
- `SessionMemory` persists to JSON, survives across process restarts
- `KnowledgeStore` writes human-readable `knowledge.md` + machine-readable JSON
- 3 new loop-based demos with proper verification

---

## Previous Progress

See `docs/superpowers/plans/2026-05-04-aether-native-phase0.md` and `2026-05-04-aether-native-phase1.md` for historical implementation details. Those documents describe what was built; this log describes what comes next.
