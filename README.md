# Aether-Native

A Linux desktop agent that watches your screen and controls your mouse/keyboard to get stuff done.

I built this because I got tired of writing brittle shell scripts for desktop automation. I wanted something that could actually *see* the screen, understand what's going on, and figure out the next step without me hardcoding coordinates.

## The Pitch

You say: "Open Brave, go to YouTube, search for that Chris Brown song, and play it"

The agent does:
1. Takes a screenshot
2. Asks a vision model "what's on screen?"
3. Asks a planner "what should I click/type next?"
4. Moves the mouse, clicks, types, waits
5. Repeats until done

No pre-recorded macros. No hardcoded coordinates. It figures it out each time.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Screenshot │────▶│  Vision Model    │────▶│  UI Elements│
│   (ffmpeg)   │     │  (OpenRouter or  │     │  (buttons,  │
│              │     │   local llava)   │     │   inputs)   │
└─────────────┘     └──────────────────┘     └─────────────┘
                                                    │
                                                    ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   ydotool   │◀────│  Planner         │◀────│  RALPH Loop │
│   (mouse/   │     │  (local Ollama   │     │  (perceive  │
│   keyboard) │     │   or OpenRouter) │     │   → plan    │
│             │     │                  │     │   → act)    │
└─────────────┘     └──────────────────┘     └─────────────┘
```

**RALPH** = the loop that keeps going: Perceive → Reason → Act → Learn

## Quickstart

You need Linux (GNOME/Wayland or X11) and a few things installed:

```bash
# Python deps
pip install -e ".[dev]"

# For Wayland mouse/keyboard control
sudo ydotoold --socket-path=/tmp/.ydotool_socket &
sudo chmod 666 /tmp/.ydotool_socket

# Optional: local models (free, slow on CPU)
ollama pull llama3.2:1b
ollama pull llava

# Required: OpenRouter API key for vision (fast, ~$0.01 per screenshot)
export OPENROUTER_API_KEY="sk-or-v1-..."
```

## Demos

```bash
# Full agent: cloud vision + cloud planning
# Needs OPENROUTER_API_KEY set
python demo_hybrid_agent.py

# Just vision: see what the model detects on screen
python demo_streaming_capture.py

# Keyboard-only: no vision, just shell commands + keystrokes
# Fastest, but less smart
python demo_keyboard_agent.py

# Mouse demo: move the cursor around
python demo_mouse.py
```

## How It Actually Works

1. **Screenshot** — ffmpeg grabs the screen silently. On Wayland it falls back to GNOME portal (which makes a sound, working on fixing that).

2. **Vision** — Sends the screenshot to a multimodal model. We use OpenRouter's `gpt-4o-mini` because it's fast (~10s) and cheap. Local `llava:7b` works too but takes ~3 minutes per image on CPU.

3. **Plan** — The vision model returns a list of UI elements with coordinates. A text LLM (either OpenRouter cloud or local Ollama) decides what to do next: click here, type this, wait, etc.

4. **Act** — ydotool executes the action on your actual desktop.

5. **Verify** — Takes another screenshot to see if anything changed. If not, retries.

## What Actually Works

- ✅ Taking screenshots via ffmpeg (silent on X11, portal fallback on Wayland)
- ✅ Cloud vision (OpenRouter gpt-4o-mini) — fast, accurate
- ✅ Cloud planning (OpenRouter gpt-4o-mini) — ~3s per plan
- ✅ Local planning (Ollama llama3.2:1b) — ~26s on CPU, but free
- ✅ Mouse/keyboard control via ydotool on Wayland
- ✅ Window focus enforcement with xdotool before typing
- ✅ Retry logic when vision API fails
- ✅ Coordinate scaling from screenshot space to display space

## What's Broken / Annoying

- ⚠️ **Credits burn fast.** 50 API calls = ~$2-3. Use local Ollama for planning to save money.
- ⚠️ **Wayland screenshots trigger GNOME sounds.** ffmpeg x11grab is silent but captures black for native Wayland apps. Portal works but beeps. No perfect solution yet.
- ⚠️ **Focus is tricky.** The agent sometimes types into the wrong window if it's not fast enough to switch. xdotool helps but isn't 100%.
- ⚠️ **Coordinates are approximate.** Vision models guess element positions. Usually close enough, but sometimes misses buttons.
- ⚠️ **Task completion detection is basic.** Checks if audio is playing and if Brave is focused. Could be smarter.

## Limitations

- Linux only. No plans for macOS/Windows.
- Wayland needs `ydotoold` running as root (kinda sketchy, but it's what we have).
- Electron apps (Discord, Spotify native) are invisible to AT-SPI, so vision is required.
- You need an OpenRouter key for decent speed. Local vision is too slow without a GPU.

## File Layout

```
aether/
├── aether/
│   ├── core/           # Loop, brain, memory, verifier
│   ├── perception/     # Screenshot, vision, AT-SPI fallback
│   ├── action/         # ydotool execution
│   ├── brain/          # Ollama and OpenRouter clients
│   └── macro/          # Macro recorder (basic)
├── tests/              # Unit + integration tests
├── demo_*.py           # Various demos
└── README.md           # This file
```

Internal docs, architecture specs, and detailed progress logs are kept locally (not in git).

## License

AGPL-3.0

## Contributing

This is a personal project but PRs are welcome. Just:
1. Run `pytest` before committing
2. Don't commit API keys (use env vars)
3. Keep it simple