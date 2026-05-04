# Aether-Native Progress Log

**Date:** 2026-05-04  
**Session:** Mouse control + Hybrid perception + Local LLM  
**Commit:** `31fd5af`

## What Was Built

### 1. Wayland Mouse Control (FIXED)
- **Problem:** Mouse jumped instantly, couldn't see it move
- **Root cause:** `ydotool mousemove` is RELATIVE by default
- **Fix:** Added `--absolute` flag + interpolated animation (30 steps/sec)
- **Result:** Mouse now glides smoothly across screen

### 2. Screenshot Capture System
- `aether/perception/screenshot.py`
- Backends: ffmpeg (XWayland) → grim (Wayland-native) → PIL (X11)
- Auto-detects best available tool
- 500ms cache to avoid repeated captures

### 3. Local LLM (Zero Cloud)
- `aether/brain/local_llm.py`
- Uses Ollama HTTP API (`curl localhost:11434/api/generate`)
- Model: `llama3.2:1b` (1.3GB, runs on CPU)
- Latency: ~200ms for simple prompts
- Methods: `generate()`, `analyze_screenshot()`, `suggest_action()`

### 4. Hybrid Perception Adapter
- `aether/perception/hybrid.py`
- **PRIMARY:** AT-SPI (<100ms, structured, exact)
- **FALLBACK:** Screenshot + Local LLM (only when AT-SPI fails)
- **NEVER:** Cloud APIs (Claude, GPT-4V, etc.)
- Tracks stats: primary vs fallback query counts

### 5. Updated UIElement Model
- Added `app` field (which application the element belongs to)
- Added `metadata` dict (for fallback context: confidence, reasoning, source)
- Made `bounds` Optional (some elements have no visible bounds)

## Test Results

```
Calculator '2' button:  ✅ AT-SPI primary, <100ms
Non-existent element:   ⚠️  AT-SPI failed → LLM fallback → not found (correct)
Mouse animation:        ✅ Smooth visible movement
Screenshot capture:     ✅ ffmpeg via XWayland, 3072x1728
```

## New Demos

| Demo | File | Description |
|------|------|-------------|
| Slow Mouse | `demo_youtube_slow.py` | Visible cursor movement to YouTube fullscreen |
| Mouse Only | `demo_youtube_mouse_only.py` | Pure mouse clicks, no keyboard |
| Hybrid Perception | `demo_hybrid_perception.py` | Shows AT-SPI primary vs LLM fallback |

## Next 3 Tasks (Priority Order)

### Task 11: Multimodal Vision Support
- `ollama pull llava` (vision model)
- Feed actual screenshot images to LLM
- Extract element positions from vision response
- **Impact:** Fallback becomes actually useful for custom UIs

### Task 12: RALPH + Hybrid Integration  
- Wire `HybridPerceptionAdapter` into `RALPHLoop`
- Before each action: capture → suggest → execute → verify
- Add retry logic and "stuck" detection
- **Impact:** System becomes truly adaptive

### Task 13: Smart Task Demos
- "Play YouTube video in Brave" end-to-end
- "Send message in Discord" (Electron, no AT-SPI)
- "Toggle Bluetooth in Settings" with verification
- **Impact:** Proves real-world utility

## Files Changed

```
aether/action/linux.py              # ydotool --absolute, smooth animation
aether/perception/screenshot.py     # NEW: ScreenshotCapture class
aether/brain/local_llm.py           # NEW: LocalLLM via Ollama HTTP API
aether/perception/hybrid.py         # NEW: HybridPerceptionAdapter
aether/core/models.py               # Added app, metadata to UIElement
docs/superpowers/plans/             # Updated Phase 1 plan with Tasks 11-13
demo_*.py                           # Multiple new demos
```

## Key Decisions

1. **Ollama HTTP API over CLI** — CLI has progress spinner noise, HTTP is clean JSON
2. **ffmpeg over grim** — grim fails on GNOME (no screen capture protocol), ffmpeg works via XWayland
3. **Text-only LLM for now** — llama3.2:1b is fast and sufficient for reasoning; vision (llava) is Task 11
4. **ydotool over python-evdev** — evdev needs `input` group permissions; ydotool daemon handles permissions

## Known Issues

- Cursor Editor demo fails (Electron on Wayland, no window focus method)
- YouTube fullscreen demo clicks approximate coordinates (not pixel-perfect)
- Vision fallback not yet implemented (Task 11)
- RALPH loop not yet using hybrid perception (Task 12)
