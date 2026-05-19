# Aether Vision-First Hybrid Agent Architecture

**Date:** 2026-05-19
**Status:** Architecture implemented, tested with limitations on CPU-only hardware

## Overview

Aether-Native now uses a **vision-first hybrid perception** architecture:

1. **Vision is PRIMARY**: Every loop step starts by capturing a screenshot and sending it to a local multimodal LLM (llava:7b) for analysis.
2. **AT-SPI is FALLBACK**: If vision times out or fails, the system falls back to the Linux accessibility tree for structured UI data.
3. **Fast execution**: Actions are executed via `ydotool` (Wayland-native, no X11 dependency).
4. **Local brain**: Planning is done by a local text LLM (nemotron3:33b or llama3.2:1b).

## Components

### 1. VisionFirstPerceptionAdapter (`aether/perception/vision_first.py`)

- **Screenshot capture**: Uses freedesktop portal (GNOME/Wayland) with ffmpeg x11grab fallback
- **Vision analysis**: Sends screenshot to llava:7b via Ollama
- **Structured output**: Parses llava's text response into `UIMap` with `UIElement` coordinates
- **Timeout**: Configurable timeout (default 120s) with automatic AT-SPI fallback
- **Coordinate scaling**: Screenshots are downscaled for speed (default 640px width)

### 2. YdotoolActionAdapter (`aether/action/ydotool.py`)

- Wayland-native mouse/keyboard control via `ydotool`
- Supports: click, right_click, type, hotkey, scroll, wait
- Requires `ydotoold` daemon running with accessible socket

### 3. RalphLoop Integration

The existing `RalphLoop` is fully compatible:
- `perception.capture()` → returns `UIMap`
- `brain.reason()` → plans actions from `UIMap`
- `action.click/type/hotkey/scroll()` → executed via ydotool

## Test Results

### What Works
- ✅ **Screenshot capture via portal**: GNOME portal successfully captures screenshots on Wayland
- ✅ **llava:7b vision analysis**: Correctly identifies UI elements in synthetic and real screenshots
- ✅ **ydotool execution**: Mouse movement, clicks, typing, hotkeys all work on Wayland
- ✅ **AT-SPI fallback**: Fast structured UI data when vision is unavailable
- ✅ **Keyboard-only agent**: Successfully opened Brave, navigated YouTube, and played audio (first run)

### Limitations on This Hardware
- ⚠️ **llava:7b is very slow on CPU**: ~3-5 minutes per screenshot analysis
  - **Mitigation**: Use GPU, smaller vision model (moondream:1.8b), or cloud vision API
- ⚠️ **Screen is dark/black to X11**: ffmpeg x11grab captures black on this GNOME/Wayland session
  - **Mitigation**: Portal capture works but returns dim images; physical display may be off
- ⚠️ **Ollama single-threaded**: One model at a time, so vision blocks planning

## Performance Numbers

| Component | Latency | Bottleneck |
|---|---|---|
| Screenshot (portal) | ~2s | Portal polling |
| Screenshot (ffmpeg) | ~1s | X11grab (black on Wayland) |
| llava:7b analysis (640px) | ~180-300s | CPU inference |
| AT-SPI tree walk | ~0.5s | Tree traversal |
| nemotron3:33b planning | ~20-60s | CPU inference |
| llama3.2:1b planning | ~2-5s | CPU inference |
| ydotool action | ~0.3s | Daemon IPC |

## Recommendations for Production

1. **Use a GPU**: llava:7b drops from ~5min to ~2sec per image on a modern GPU
2. **Use moondream:1.8b**: 3x smaller than llava, much faster on CPU
3. **Use cloud vision API** (OpenAI GPT-4V, Claude 3): Fastest but requires internet
4. **Cache vision results**: Don't re-analyze static UI elements
5. **Run Ollama on a separate machine** with GPU and expose via network

## Files Added/Modified

- `aether/perception/vision_first.py` — NEW: Vision-first perception with AT-SPI fallback
- `aether/action/ydotool.py` — NEW: Wayland-native action adapter
- `aether/core/safety.py` — Added `DummySafetyChecker`
- `aether/core/verify.py` — Added `DummyVerifier`
- `demo_vision_first.py` — NEW: Full vision-first agent demo
- `demo_keyboard_agent.py` — NEW: Fast keyboard-only agent (no vision)
- `aether_deskctl.sh` — NEW: Bash helper for ydotool + screenshot
- `demo_live_agent.py` — NEW: Interactive agent with llava + nemotron3

## Next Steps

1. Test with GPU-accelerated Ollama (llava drops to <5s)
2. Integrate `moondream:1.8b` for faster CPU vision
3. Add vision result caching to avoid re-analyzing static screens
4. Implement parallel perception (vision + AT-SPI simultaneously)
5. Add retry logic for failed screenshots