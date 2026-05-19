# Aether-Native

Local-first, Linux-native computer-use agent.

## What It Does

Aether-Native controls your Linux desktop autonomously. You describe a task in natural language; it perceives the UI via the accessibility tree (AT-SPI), reasons about what to do using a local LLM, executes mouse/keyboard actions, verifies the result, and learns from failures.

**Key difference from cloud agents:** No screenshots are sent to Claude, GPT-4V, or any remote API. Perception happens via the OS accessibility tree (<100ms, pixel-perfect). A local multimodal model (`llava` via Ollama) is used only as a fallback when the accessibility tree is insufficient.

## Quickstart

### Prerequisites

- Linux with GNOME (Wayland or X11)
- Python 3.11+
- `uv` (package manager)
- Ollama running locally
- `ydotool` daemon (for Wayland input)

### Install

```bash
# Clone and install
uv pip install -e ".[dev]"

# Pull required models
ollama pull llama3.2:1b
ollama pull llava

# Start ydotool daemon (Wayland only)
sudo ydotoold &
```

### Run

```bash
# Run a task
aether run "Open calculator and compute 2+2"

# Or use the Python API
python -m aether.cli run "Toggle Bluetooth in Settings"
```

### Test

```bash
# Unit tests (fast, headless)
pytest tests/test_core/ -v

# Integration tests (requires real desktop)
pytest tests/test_integration.py -v -m integration
```

## Architecture

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

**RALPH** = Reasoning, Action, Learning, Progress, History

## How It Works

1. **Perceive:** Captures the UI state via AT-SPI2 accessibility tree. If the tree is empty (e.g., Electron app), falls back to a screenshot analyzed by `llava`.
2. **Reason:** The local LLM (`llama3.2:1b`) analyzes the UI state + task + history and generates a structured action plan (JSON).
3. **Execute:** Performs clicks, typing, hotkeys, or shell commands via `ydotool` (Wayland) or `python-xlib` (X11).
4. **Verify:** Checks that the UI state changed as expected. If not, triggers a retry with learned context.
5. **Learn:** Writes successful patterns and failure workarounds to `~/.local/share/aether/memory.json` and `knowledge.md`.

## Current Status

**This is a Linux-only Python project.** Earlier documentation mentioned Rust, cross-platform adapters, and features like Ghost Overlay / Voice Control. Those were premature design fantasies. The current focus is making the Linux agent robust and autonomous.

### What Works Today
- AT-SPI tree scraping with <100ms latency
- Mouse/keyboard control on Wayland and X11
- Screenshot capture (ffmpeg/grim/PIL)
- Local LLM reasoning via Ollama
- Safety checker (command blacklist, bounds checking)
- Self-healing macro recorder/player (basic)

### What's Being Built Now
See `docs/superpowers/specs/2026-05-19-aether-native-revised-design.md` for the current implementation plan.

### Known Limitations
- Linux only (no macOS/Windows support planned until the Linux agent is solid)
- Requires Ollama running locally
- Wayland users need `ydotoold` daemon
- Electron apps (Discord, Slack, Cursor) have limited AT-SPI support; vision fallback is required

## Project Structure

```
aether/
├── aether/
│   ├── core/           # RALPH loop, brain, memory, safety, verify
│   ├── perception/     # AT-SPI, screenshot, hybrid adapter
│   ├── action/         # Linux input (ydotool, Xlib)
│   ├── brain/          # Local LLM integration (Ollama)
│   ├── macro/          # Self-healing macro recorder/player
│   ├── api/            # FastAPI stub
│   └── prompts/        # LLM prompt templates
├── tests/
│   ├── test_core/      # Unit tests
│   ├── test_integration.py  # End-to-end desktop tasks
│   └── fixtures/       # Mock UI states
├── docs/
│   └── superpowers/
│       ├── specs/      # Design documents
│       └── plans/      # Implementation plans
├── knowledge.md        # Learned UI quirks (auto-generated)
└── pyproject.toml
```

## Documentation

- **Design Spec:** `docs/superpowers/specs/2026-05-19-aether-native-revised-design.md`
- **Phase 0 Plan:** `docs/superpowers/plans/2026-05-04-aether-native-phase0.md` (historical)
- **Phase 1 Plan:** `docs/superpowers/plans/2026-05-04-aether-native-phase1.md` (historical)
- **Progress Log:** `PROGRESS.md`

## License

AGPL-3.0

## Contributing

1. Write a failing test first (TDD)
2. Make it pass with minimal code
3. Run `pytest`, `ruff check .`, `mypy aether/`
4. Update `PROGRESS.md` with what you built and why
