# Aether-Native

Local-first, Linux-native computer-use agent with optional cloud vision.

## What It Does

Aether-Native controls your Linux desktop autonomously. You describe a task in natural language; it perceives the UI via screenshots (analyzed by cloud vision or local llava), reasons about what to do using a local or cloud LLM, executes mouse/keyboard actions via ydotool, verifies the result, and learns from failures.

**Key difference from cloud agents:** Perception uses screenshots + vision (multimodal), but reasoning and execution happen locally. No data leaves your machine except the screenshot pixels sent to the vision API.

## Architecture

```
User Task
    |
    v
+-----------+     +------------------+     +---------+
|  RALPH    |<--->| Vision-First     |<--->| Screenshot|
|  Loop     |     | Perception       |     | Capture  |
+-----------+     +------------------+     +---------+
    |  ^                |                           |
    |  |                v                           v
    |  |           +---------+                +----------+
    |  |           | AT-SPI  |                | ffmpeg   |
    |  |           |Fallback |                | portal   |
    |  |           +---------+                +----------+
    |  |
    v  |
+-----------+     +---------+     +----------+
|  Brain    |     |  Linux  |     |  Verify  |
| (Local/   |     | Action  |     | (Desktop)|
|  Cloud)   |     | ydotool |     |          |
+-----------+     +---------+     +----------+
```

## Quickstart

### Prerequisites

- Linux with GNOME (Wayland or X11)
- Python 3.11+
- `uv` (package manager)
- Ollama running locally (for local planning)
- `ydotool` daemon (for Wayland input)
- OpenRouter API key (for cloud vision, optional but recommended)

### Install

```bash
# Clone and install
uv pip install -e ".[dev]"

# Pull local models (optional, for local planning)
ollama pull llama3.2:1b
ollama pull llava

# Start ydotool daemon (Wayland only)
sudo ydotoold --socket-path=/tmp/.ydotool_socket &
sudo chmod 666 /tmp/.ydotool_socket
```

### Run

```bash
# Full cloud agent (OpenRouter vision + planning)
python demo_full_cloud_agent.py

# Local agent (Ollama planning + OpenRouter vision)
python demo_cloud_vision_agent.py

# Keyboard-only agent (no vision, fastest)
python demo_keyboard_agent.py
```

### Test

```bash
# Unit tests (fast, headless)
pytest tests/test_core/ -v

# Vision test (requires OpenRouter API key)
python demo_openrouter_vision.py
```

## How It Works

1. **Perceive:** Captures screenshot via GNOME portal or ffmpeg. Sends to vision model (OpenRouter cloud or local llava) for UI element detection. Falls back to AT-SPI accessibility tree.
2. **Reason:** LLM analyzes the UI state + task + history and generates a single action (click, type, key, shell, wait, scroll).
3. **Execute:** Performs actions via `ydotool` (Wayland) or `python-xlib` (X11).
4. **Verify:** Checks that the UI state changed (process running, audio playing, screen brightness changed, active window changed).
5. **Learn:** Re-plans after every action. Writes successful patterns to memory.

## Current Status

### What Works Today ✅

- **Screenshot capture:** GNOME portal (Wayland) + ffmpeg x11grab (X11) + retry logic
- **Cloud vision:** OpenRouter gpt-4o-mini (~10s, excellent accuracy)
- **Local vision:** llava:7b via Ollama (~180s on CPU)
- **Cloud planning:** OpenRouter gpt-4o-mini (~3s)
- **Local planning:** llama3.2:1b via Ollama (~5s)
- **Action execution:** Mouse (click, move), keyboard (type, hotkey, key), scroll, shell
- **Verification:** Process check, audio detection, brightness diff, window change
- **Focus enforcement:** Detects wrong window, switches with alt+Tab before typing
- **Coordinate scaling:** Scales vision coordinates from screenshot space to display space
- **Retry logic:** Auto-resizes screenshot on API errors, retries 3x

### Current Blockers ⚠️

1. **OpenRouter credits:** Depletes after ~50 API calls. Switching to local planning.
2. **Window focus:** Agent sometimes types into wrong window. Need better focus management.
3. **Screenshot noise:** GNOME portal triggers sound + flash. Need silent capture method.
4. **Task completion:** Returns "success" prematurely. Needs better done-detection.

### Known Limitations

- Linux only (no macOS/Windows support planned)
- Wayland users need `ydotoold` daemon running as root
- Electron apps have limited AT-SPI support; vision fallback required
- Coordinate accuracy varies (vision model returns approximate positions)
- OpenRouter API costs accumulate quickly for development

## Project Structure

```
aether/
├── aether/
│   ├── core/           # RALPH loop, brain, memory, safety, verify
│   ├── perception/     # Vision-first, AT-SPI, hybrid adapter
│   ├── action/         # ydotool, Xlib
│   ├── brain/          # Local LLM (Ollama), OpenRouter cloud
│   ├── macro/          # Self-healing macro recorder/player
│   ├── api/            # FastAPI stub
│   └── prompts/        # LLM prompt templates
├── tests/
│   ├── test_core/      # Unit tests
│   ├── test_integration.py
│   └── fixtures/       # Mock UI states
├── docs/
│   └── superpowers/
│       ├── specs/      # Design documents
│       └── plans/      # Implementation plans
├── knowledge.md        # Learned UI quirks (auto-generated)
├── PROGRESS.md         # Detailed progress log
└── pyproject.toml
```

## Upcoming Features

### ffmpeg Video Recording

Instead of capturing individual screenshots (which triggers GNOME notifications), we're integrating **continuous video recording**:

```bash
# Background: record screen at low resolution
ffmpeg -f x11grab -i :0 -vf "scale=320:-1,fps=0.5" -f image2pipe pipe:1

# Agent samples latest frame on demand — no capture delay, no notifications
```

**Benefits:**
- Zero per-capture delay (frame already captured)
- No GNOME portal notifications/sounds
- Enables real-time observation
- Lower CPU overhead than repeated captures

**Tradeoff:** Constant CPU usage (~5-10% for 320x180 @ 0.5fps)

### Hybrid Cloud/Local Mode

```
Screenshot → OpenRouter Vision (fast, multimodal)
     ↓
Local Plan (llama3.2:1b via Ollama — free, fast)
     ↓
ydotool Action
```

**Cost:** ~1/3 of full cloud mode. Vision is the expensive part; planning is cheap locally.

## Documentation

- **Progress Log:** `PROGRESS.md` (detailed session-by-session log)
- **Design Spec:** `docs/superpowers/specs/2026-05-19-aether-native-revised-design.md`
- **Vision Architecture:** `docs/superpowers/specs/2026-05-19-vision-first-architecture.md`
- **Phase A Plan:** `docs/superpowers/plans/2026-05-19-close-the-loop.md`

## License

AGPL-3.0

## Contributing

1. Write a failing test first (TDD)
2. Make it pass with minimal code
3. Run `pytest`, `ruff check .`, `mypy aether/`
4. Update `PROGRESS.md` with what you built and why