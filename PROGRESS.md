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

### Phase A: Close the Loop (Week 1)

- [ ] **Task 1: Replace `StubBrain` with `LocalLLMBrain`**
  - Implement real prompt rendering from `prompts/planner.j2`
  - Parse JSON ActionPlan from LLM response with validation + retry
  - Wire into `RalphLoop`

- [ ] **Task 2: Make `HybridPerceptionAdapter` the default**
  - Inject into `RalphLoop` constructor
  - Ensure AT-SPI primary path is used first

- [ ] **Task 3: Real vision fallback with `llava`**
  - `ollama pull llava`
  - Encode screenshot as base64 PNG
  - POST to `/api/generate` with `images` field
  - Parse coordinates from response

- [ ] **Task 4: Persistent memory**
  - `SessionMemory` loads/saves `~/.local/share/aether/memory.json`
  - Atomic writes
  - Stores history, failed_attempts, progress, knowledge

- [ ] **Task 5: KnowledgeStore**
  - Writes to `knowledge.md` (human-readable) + `knowledge.json` (machine-readable)
  - Injects relevant knowledge into LLM prompt before reasoning

### Phase B: Verified End-to-End Tasks (Week 2)

- [ ] **Task 6: Calculator e2e test**
  - Open calculator, compute 2+2, verify display shows 4
  - AT-SPI primary path
  - Integration test with `@pytest.mark.integration`

- [ ] **Task 7: YouTube fullscreen e2e test**
  - Open Brave, navigate to known video, make fullscreen
  - Hybrid perception (AT-SPI for browser, vision/keyboard fallback for player)
  - Verify via screenshot diff (no window decorations)

- [ ] **Task 8: Bluetooth toggle e2e test**
  - Open GNOME Settings, navigate to Bluetooth, toggle switch
  - Verify via AT-SPI state change

- [ ] **Task 9: Delete 12 old demos, keep 1 sanity demo**
  - `demo.py` as quick smoke test
  - All others replaced by integration tests

### Phase C: Polish (Week 3)

- [ ] **Task 10: Screenshot diff verifier**
  - Perceptual hashing fallback when tree diff is inconclusive
  - Needed for "did the video actually go fullscreen?"

- [ ] **Task 11: Improve error handling and retry logic**
  - Better messages when `ydotoold` is not running
  - Retry on `ydotool` command drop
  - "Stuck" detection (same state 3x in a row)

- [ ] **Task 12: Update all documentation**
  - README.md (done)
  - Aether-Native_Blueprint.md (done)
  - Design spec (done)
  - Inline docstrings

- [ ] **Task 13: CLI command `aether run "task description"`**
  - Currently `aether` only has stub commands
  - Make `run` actually execute the RALPH loop

### Phase D: Testing & Quality

- [ ] **Task 14: Unit test coverage >90% on core modules**
  - Mock `urllib.request` for `local_llm.py`
  - Mock `subprocess` for `screenshot.py`
  - Mock AT-SPI for `hybrid.py`

- [ ] **Task 15: Integration test harness**
  - Runs e2e tasks in a controlled desktop session
  - Reports ALR score

- [ ] **Task 16: ruff + mypy clean**
  - Fix all lint errors
  - Fix all type errors

---

## Key Decisions

1. **Python, not Rust.** The existing Python stack works. Rewriting would be 6 months of zero user value.
2. **Linux, not cross-platform.** One working OS beats three broken stubs.
3. **Ollama HTTP API over `llama-cpp-python`.** HTTP is simpler, no complex bindings, easy to mock in tests.
4. **3 verified tasks over 12 demos.** Quality over quantity. Every task must prove itself.
5. **Persistence is not optional.** An agent that forgets everything on exit is not an agent.

## Known Issues (To Fix)

- `StubBrain` hardcodes actions
- `HybridPerceptionAdapter` not wired into `RalphLoop`
- `LocalLLM.analyze_screenshot()` is text-only fakery
- No memory persistence
- No `knowledge.md`
- 0% coverage on `linux.py`, `hybrid.py`, `screenshot.py`, `local_llm.py`
- 12 unverified demo scripts

---

## Previous Progress

See `docs/superpowers/plans/2026-05-04-aether-native-phase0.md` and `2026-05-04-aether-native-phase1.md` for historical implementation details. Those documents describe what was built; this log describes what comes next.
