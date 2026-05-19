# Aether-Native: Project Blueprint

**Version:** 2.0 (Revised 2026-05-19)
**Platform:** Linux (Fedora/GNOME/Wayland primary, Ubuntu/X11 secondary)
**Objective:** Build a Linux-native computer-use agent that eliminates the latency and precision issues of cloud-based vision models by leveraging OS-level accessibility trees and local inference.

---

## Important Note: Scope Revision

This blueprint was originally written targeting Rust, cross-platform support (macOS/Windows), and features like Ghost Overlay and Voice Control. **Those goals were premature.** The current codebase is Python, Linux-only, and focused on closing the RALPH loop with a real brain, persistent memory, and verified task completion.

**Do not implement cross-platform adapters, Ghost Overlay, or Voice Control until the Linux agent achieves >90% success on the 3 verified end-to-end tasks.**

For the current authoritative design, see:
`docs/superpowers/specs/2026-05-19-aether-native-revised-design.md`

---

## 1. The RALPH Loop Framework

To allow an agent to operate autonomously, we utilize the **RALPH (Reasoning, Action, Learning, Progress, History)** loop.

* **Reasoning:** Analyze the current UI state (AT-SPI Tree + optional vision fallback) vs. the user goal.
* **Action:** Execute specific input commands via ydotool (Wayland) or python-xlib (X11).
* **Learning:** Update `knowledge.md` and `memory.json` with UI quirks (e.g., "The fullscreen button in Brave is unreliable; use the 'f' key instead").
* **Progress:** Track sub-task completion in persistent memory.
* **History:** Log action sequences to avoid repeating failed paths.

---

## 2. Architecture (High-Level)

Aether-Native is a **Local-First Hybrid Agent**. Unlike existing tools that rely solely on sending full-resolution screenshots to a cloud VLM, Aether-Native treats the Operating System as a structured data source.

### 2.1 Hybrid Perception System

The core innovation is the separation of "seeing" into two distinct channels:

* **Structural Channel (Primary):** Queries the `AT-SPI2` (Accessibility Bus) to retrieve a text-based tree of all UI elements. This provides 100% accurate coordinates without visual inference. Latency: <100ms.
* **Visual Channel (Auxiliary):** Uses a local multimodal model (`llava` via Ollama) to analyze screenshots only when the structural channel fails — such as interpreting Electron apps, games, or custom-drawn UIs. Latency: 1-3s.

### 2.2 The Controller Loop

The system operates on the **Observer-Reason-Act-Verify-Learn** pattern, running entirely within the local user session.

```text
[OS UI State (AT-SPI)] -> [UIMap] -> [Local LLM (llama3.2:1b)]
                                              |
[Action Sequence (JSON)] <- [Reasoning / Task Planning]
      |
[ydotool / Xlib] -> [Wayland Compositor / X11]
      |
[Verify: New UI State] -> [Match expected_change?]
      |
[Learn: Persist success/failure to memory]
```

---

## 3. Design Document (Component Details)

The design focuses on modularity, allowing the "Brain" to be swapped while keeping the "Hands" (input) and "Eyes" (perception) stable.

### 3.1 Perception Module (`aether/perception/`)

This module acts as the translator. It converts the D-Bus AT-SPI tree into a **Semantic UI Map**.

* **Target:** `org.a11y.Bus`
* **Functionality:** Recursively walk the accessibility tree. Filter out invisible nodes.
* **Output:** A compressed Markdown snippet (e.g., `[42] Button: "Submit" (x:400, y:300)`) for the LLM prompt.
* **Fallback:** If the tree is empty or the target element is missing, capture a screenshot and invoke `llava` for visual analysis.

### 3.2 Execution Module (`aether/action/linux.py`)

Implements physical input injection on Linux.

* **Wayland:** `ydotool` daemon for mouse and keyboard events.
* **X11:** `python-xlib` for precise pointer warping and synthetic events.
* **Features:** Smooth mouse animation (interpolated movement, 30 steps/sec).

### 3.3 Reasoning Module (`aether/brain/local_llm.py`)

Uses a **Local Inference Engine** to process tasks.

* **Text Model:** `llama3.2:1b` (1.3GB, ~200ms for simple prompts) for task planning and reasoning.
* **Vision Model:** `llava` (multimodal, ~1-2s) for screenshot analysis when AT-SPI fails.
* **Backend:** Ollama HTTP API (`localhost:11434`)
* **Structured Output:** JSON ActionPlan with Pydantic validation. Retry on malformed output.

---

## 4. Implementation Document (Technical Stack)

| Component | Technology | Reasoning |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ | Existing codebase, fast iteration, huge ecosystem |
| **Package Manager** | `uv` | Modern, fast lockfile |
| **Input Injection (Wayland)** | `ydotool` | Modern Wayland standard, no root needed with daemon |
| **Input Injection (X11)** | `python-xlib` | Precise, mature |
| **Accessibility (Linux)** | `pyatspi2` | Mature, well-documented |
| **Screenshot** | `ffmpeg` / `grim` / `PIL` | Auto-detects best available tool |
| **Inference** | Ollama HTTP API | Simple, no complex bindings |
| **Text Model** | `llama3.2:1b` | Fast, sufficient for reasoning |
| **Vision Model** | `llava` | Actually sees screenshots |
| **Testing** | `pytest` + `pytest-asyncio` | Universal, well-known |
| **Linting** | `ruff` | Fast, replaces flake8/black/isort |
| **Type Checking** | `mypy` | Catches bugs early |

### 4.1 Folder Structure

```text
aether/
├── aether/
│   ├── cli.py                   # Typer CLI entrypoint
│   ├── core/
│   │   ├── loop.py              # RALPH loop orchestrator
│   │   ├── brain.py             # Brain ABC (LocalLLMBrain implementation)
│   │   ├── memory.py            # Session memory with persistence
│   │   ├── knowledge.py         # KnowledgeStore (knowledge.md + JSON)
│   │   ├── verify.py            # State verification
│   │   ├── safety.py            # Action safety checker
│   │   └── models.py            # Pydantic models (UIMap, ActionPlan, etc.)
│   ├── perception/
│   │   ├── base.py              # PerceptionAdapter ABC
│   │   ├── linux.py             # AT-SPI2 perception
│   │   ├── screenshot.py        # Screenshot capture (ffmpeg/grim/PIL)
│   │   └── hybrid.py            # HybridPerceptionAdapter (default)
│   ├── action/
│   │   ├── base.py              # ActionAdapter ABC
│   │   └── linux.py             # ydotool / python-xlib
│   ├── brain/
│   │   └── local_llm.py         # Ollama client (text + vision)
│   ├── macro/
│   │   ├── recorder.py          # MacroRecorder
│   │   ├── player.py            # MacroPlayer (self-healing)
│   │   └── models.py            # Macro, Intent, ElementSelector
│   ├── api/                     # FastAPI stub (future expansion)
│   └── prompts/
│       └── planner.j2           # Jinja2 prompt template
├── tests/
│   ├── test_core/               # Unit tests (models, safety, memory, verify, loop, brain)
│   ├── test_integration.py      # End-to-end integration tests (3 verified tasks)
│   ├── harness.py               # MockAdapter + fixture loader
│   └── fixtures/                # JSON UI state fixtures
├── knowledge.md                 # Long-term agent memory of UI behaviors (auto-generated)
├── memory.json                  # Machine-readable task memory (auto-generated)
├── pyproject.toml
├── README.md
└── PROGRESS.md
```

---

## 5. Requirements & Testing

### 5.1 Functional Requirements

* **FR1:** Agent must locate and click elements in the AT-SPI tree with >98% accuracy.
* **FR2:** Loop latency (Observation to Action) must be <800ms when using AT-SPI primary path.
* **FR3:** Must support multi-step macros (e.g., terminal commands followed by UI interaction).
* **FR4:** Must complete 3 verified end-to-end tasks autonomously:
  1. Calculator: compute 2+2, verify display shows 4
  2. YouTube: open Brave, play video, make fullscreen
  3. Settings: toggle Bluetooth, verify state changed
* **FR5:** Must persist learned knowledge across sessions.

### 5.2 Testing Strategy

1.  **Unit Tests:** All core modules tested with mocks. Target: >90% coverage.
2.  **Integration Tests:** 3 end-to-end tasks run against a real Linux desktop. Marked with `@pytest.mark.integration`.
3.  **Regression Tests:** One fixture per known UI quirk or bug.

---

## 6. Evaluation Framework

Success is measured by the **ALR Score (Action-Latency-Reliability)**:

$$ALR = (Success Rate \times 100) / Latency Seconds$$

### Comparison Metrics:

| Metric | Perplexity / Claude | Aether-Native |
| :--- | :--- | :--- |
| **Latency** | 3.5s - 6s | **0.2s - 0.8s** (AT-SPI primary) |
| **Grounding** | Pixel-based (Drift) | **OS-Tree (Precise)** |
| **Privacy** | Cloud-transmitted | **On-Device (Local)** |
| **Vision Fallback** | Primary method | **Rarely needed** |

---

**Note for Agent Initialization:** Start by wiring the `HybridPerceptionAdapter` into the `RalphLoop` and replacing `StubBrain` with `LocalLLMBrain`. The goal is a closed loop: perceive → reason → act → verify → learn. Everything else is secondary.
