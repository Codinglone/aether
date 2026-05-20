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

All demos live in `demos/`. Run them from the repo root (so imports work):

```bash
# Full agent: cloud vision + cloud planning
# Needs OPENROUTER_API_KEY set
python demos/demo_hybrid_agent.py

# Just vision: see what the model detects on screen
python demos/demo_streaming_capture.py

# Keyboard-only: no vision, just shell commands + keystrokes
# Fastest, but less smart
python demos/demo_keyboard_agent.py

# Mouse demo: move the cursor around
python demos/demo_mouse.py
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

## What I Learned

**Single-action planning is non-negotiable.** I tried letting the planner generate 3 actions at once. Every time, the second or third action was wrong because the screen had already changed after the first action. Now it plans 1 action, executes it, and re-perceives.

**Cloud vision is worth paying for.** `llava:7b` on CPU takes ~3 minutes to analyze a screenshot. OpenRouter's `gpt-4o-mini` takes ~10 seconds. That's the difference between "this works" and "this is unusable."

**Focus is harder than I thought.** I assumed typing would go where the mouse was. Nope — it goes to whatever window X11 thinks is focused. And on Wayland that's even messier. xdotool helps but isn't perfect.

**Portal screenshots are noisy.** Every GNOME portal capture triggers a camera-shutter sound and a visual flash. ffmpeg x11grab is silent but captures black for native Wayland apps. No clean solution yet — it's either noisy or incomplete.

**Coordinates lie.** The vision model says "button at (500, 300)" but that's relative to the 640px screenshot, not your actual 1920x1080 or 3072x1728 display. You have to scale them, and even then it's approximate.

**Credits vanish faster than you expect.** 50 API calls burned ~$2-3 in one afternoon of testing. That's fine for occasional use, but for development you want local planning (Ollama) and only pay for vision.

## What Would Make This Way Better

**GPU for local vision.** If I had a GPU, `llava:7b` would drop from ~180s to ~2s per image. Then I wouldn't need OpenRouter at all. That's the biggest bottleneck.

**A smaller vision model.** `moondream:1.8b` is supposedly much faster on CPU than `llava:7b`. Haven't tested it yet but it's on the list.

**Caching vision results.** The desktop background and taskbar don't change between screenshots. Why re-analyze them every time? Cache static elements and only look at what changed.

**Continuous video recording.** Instead of capturing a screenshot every 10 seconds, run ffmpeg in the background recording at 0.5 fps. Grab the latest frame instantly when you need it. No per-capture delay, no portal noise.

**Learned action sequences.** After the agent successfully opens YouTube and searches a few times, it should remember the sequence. Next time, skip the vision + planning and just execute the cached steps.

**Better focus control.** Instead of `alt+Tab` guessing, use `wmctrl -a <window_id>` or `xdotool windowfocus <id>` to explicitly focus the target window before typing.

**Multiple completion signals.** Right now I just check "is audio playing?" A better check would be: is Brave focused? Does the URL contain "youtube.com/watch"? Is there a pause button visible? Combine all three.

**PipeWire for audio.** `pactl` is a compatibility layer. Using PipeWire directly might give more accurate per-app audio detection.

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
├── demos/              # Demo scripts
├── tests/              # Unit + integration tests
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