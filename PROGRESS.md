# Aether-Native Progress Log

**Date:** 2026-05-19
**Session:** Full cloud agent architecture — OpenRouter vision + planning, ydotool execution
**Branch:** `feature/close-the-loop` → **MERGED INTO MAIN**
**Status:** Architecture complete, all changes on main

---

## Security Note

**OpenRouter API key was accidentally committed to git history** (commits `32e09df` and `e85368b`).
- **Status:** ✅ Key has been revoked/deleted by user
- **Current code:** Uses `OPENROUTER_API_KEY` environment variable (no hardcoded keys)
- **Sudo password:** Never committed to repo (only in conversation)
- **Repo safety:** Safe to make public — exposed key is revoked

---

## What Was Built Today

### 1. Full Cloud Agent (`demo_full_cloud_agent.py`)

A complete end-to-end agent loop using cloud APIs for intelligence and local tools for execution:

```
Screenshot → OpenRouter Vision (gpt-4o-mini) → OpenRouter Plan (gpt-4o-mini) → ydotool Action
     ↑                                                                  ↓
     └────────────────── Verify (DesktopVerifier) ──────────────────────┘
```

**Performance:**
- Vision: ~8-12s per screenshot (640px PNG)
- Planning: ~3-5s per action plan
- Action execution: ~0.3s (ydotool)
- Full loop: ~10-15s per iteration

### 2. New Components

| Component | File | Purpose |
|---|---|---|
| `VisionFirstPerceptionAdapter` | `aether/perception/vision_first.py` | Cloud vision (OpenRouter) with AT-SPI fallback |
| `OpenRouterBrain` | `aether/brain/openrouter.py` | Cloud planning via gpt-4o-mini |
| `YdotoolActionAdapter` | `aether/action/ydotool.py` | Wayland-native mouse/keyboard |
| `DesktopVerifier` | `aether/core/desktop_verify.py` | Real-time verification (processes, audio, brightness) |
| `OpenRouterVisionClient` | `aether/perception/openrouter_vision.py` | Reusable OpenRouter vision client |

### 3. Key Features

- **Retry logic**: Vision retries 3x on HTTP errors, auto-resizes screenshot on 400 errors
- **Coordinate scaling**: Screenshot coordinates (320-640px) scaled to actual display (3072x1728)
- **App detection**: Vision model identifies foreground app (Brave, Firefox, VS Code, etc.)
- **Focus enforcement**: Before typing, checks if target app is active; switches with `alt+Tab` if not
- **Task completion**: Detects audio playback from target app (e.g. Brave) to determine if video is playing
- **Non-blocking shell**: Opens browsers via `Popen` without hanging the loop

### 4. Continuous Video Recording (`aether/perception/video_recorder.py`)

A background ffmpeg process continuously captures the screen:

```python
recorder = VideoRecorder(width=640, fps=0.5)
recorder.start()
# ... anytime ...
frame_path = recorder.get_latest_frame()  # Instant, no capture delay
```

**How it works:**
1. ffmpeg runs in background with `-update 1` (continuously overwrites same file)
2. Frame is always available in `/tmp/aether_latest_frame.jpg`
3. No per-capture delay — just read the file
4. No GNOME portal notifications for X11/XWayland apps

**Limitations:**
- On pure Wayland: x11grab captures black, auto-switches to portal (notifications)
- Portal still triggers sound + flash on Wayland native apps
- Constant CPU usage: ~5% for 640px @ 0.5fps

**Next:** Suppress GNOME sounds temporarily during portal capture

### 5. Test Results

**Task:** "Open Brave browser, go to YouTube, search for 'International love chris brown', and play the first video"

- ✅ Vision queries: 100% success rate (was ~20% before retry logic)
- ✅ Brave opens via shell command
- ✅ ydotool executes clicks, typing, hotkeys
- ✅ DesktopVerifier detects audio playback
- ⚠️ **Focus issue**: Agent sometimes types into wrong window when Brave is not foreground
- ⚠️ **Loop termination**: Returns "success" after max retries even if task incomplete
- ⚠️ **Coordinate accuracy**: Click coordinates from vision don't always hit intended targets

---

## Current Blockers

### 1. OpenRouter Credits Depleted
- **Status:** `402 Payment Required` on planning calls
- **Impact:** Agent cannot run without credits
- **Mitigation:** Switch to local Ollama for planning (llama3.2:1b), keep OpenRouter for vision only
- **Cost so far:** ~50 API calls (vision + planning) consumed ~$2-3

### 2. Window Focus Management
- **Problem:** Agent types into whatever window is focused, not necessarily Brave
- **Root cause:** `ydotool` synthetic events go to focused window; shell command opens Brave but doesn't focus it
- **Attempted fix:** `_enforce_app_focus()` checks active app before typing, switches with `alt+Tab`
- **Issue:** Vision-detected app name is unreliable; `active_window` often `None` or "unknown"

### 3. Coordinate Scaling
- **Problem:** Vision model returns coordinates in 1920x1080 screenshot space, but display is 3072x1728
- **Attempted fix:** `_scale_coords()` multiplies by display/screenshot ratio
- **Issue:** Portal screenshots are 1920x1080, but ffmpeg x11grab captures black screen; coordinate mapping uncertain

### 4. Screenshot Capture Annoyance
- **Problem:** GNOME portal screenshot triggers sound + visual flash every capture
- **Impact:** Highly annoying for continuous agent loops
- **Options:**
  - Suppress GNOME sounds temporarily
  - Use silent `ffmpeg x11grab` (captures black on Wayland)
  - Use `kmsgrab` with sudo (raw framebuffer, no compositor)
  - **Continuous video recording** with ffmpeg (background stream, sample frames on demand)

---

## Ideas & Next Steps

### Short Term (This Week)

1. **Switch to hybrid cloud/local**
   - OpenRouter for vision only (fast, multimodal)
   - Local Ollama (llama3.2:1b) for planning (free, fast enough on CPU)
   - Reduces API cost by ~60%

2. **Fix focus management**
   - Use `wmctrl` or `xdotool` to explicitly raise/focus Brave window
   - Or: always click on the target input field before typing
   - Or: use `ydotool` to click on the browser window to focus it first

3. **Better task completion detection**
   - Check for specific UI elements ("Pause" button visible = video playing)
   - Check URL bar contents (contains "youtube.com/watch")
   - Check process command line (Brave launched with YouTube URL)

### Medium Term (Next 2 Weeks)

4. **Silent screenshot capture**
   - Implement ffmpeg-based capture as primary (no portal notifications)
   - Add `silent=True` parameter to `VisionFirstPerceptionAdapter`
   - Investigate PipeWire screen capture for Wayland-native silent capture

5. **Continuous video recording**
   - Background ffmpeg process records low-res stream (320x180 @ 0.5fps)
   - Agent samples latest frame when needed (no capture delay)
   - Enables real-time observation without per-frame API costs
   - Tradeoff: Constant CPU usage (~5-10%)

6. **Mouse movement visualization**
   - Show where the agent is clicking in real-time
   - Helps debug coordinate accuracy issues
   - Could overlay a cursor indicator

### Long Term (Next Month)

7. **Learned action sequences**
   - Cache successful action sequences for common tasks
   - "Open YouTube and search" becomes a single learned macro
   - Reduces API calls and improves speed

8. **Multi-app workflows**
   - Copy text from one app, paste into another
   - Drag-and-drop between windows
   - Requires better window management

9. **Error recovery**
   - Detect when agent is stuck (same state 3x in a row)
   - Automatic screenshot + human intervention request
   - Fallback to simpler strategies

---

## Architecture Evolution

### Original Design (Local Only)
```
AT-SPI → Local LLM (nemotron3:33b) → ydotool
  ↑___________________________________↓
```
**Issue:** nemotron3:33b is ~60s per plan; llava:7b is ~180s per vision

### Current Design (Full Cloud)
```
Screenshot → OpenRouter Vision → OpenRouter Plan → ydotool
     ↑_________________________________________________↓
```
**Issue:** Fast but expensive; credits deplete quickly

### Target Design (Hybrid)
```
Screenshot → OpenRouter Vision (fast, multimodal) → Local Plan (llama3.2:1b) → ydotool
     ↑______________________________________________________________↓
```
**Benefit:** Best of both worlds; fast vision + free planning

---

## Key Changes Today

| File | Change |
|---|---|
| `aether/perception/vision_first.py` | OpenRouter cloud vision with retry logic, coordinate scaling, app detection |
| `aether/brain/openrouter.py` | Cloud planning with single-action-per-plan, better prompts |
| `aether/action/ydotool.py` | Wayland-native action adapter with `key()` method |
| `aether/core/loop.py` | Re-plan after every action, focus enforcement, task completion detection |
| `aether/core/desktop_verify.py` | Real verifier (processes, audio, brightness, window changes) |
| `aether/core/safety.py` | Added `DummySafetyChecker` |
| `aether/core/verify.py` | Added `DummyVerifier` |
| `demo_full_cloud_agent.py` | End-to-end cloud agent demo |
| `aether_deskctl.sh` | Bash helper for ydotool + screenshot |

---

## Lessons Learned

1. **Cloud vision is worth it.** llava:7b on CPU = ~180s/image. OpenRouter gpt-4o-mini = ~10s/image. The speed difference is massive.
2. **Single-action planning is essential.** Multi-action plans based on stale screenshots always fail when the UI changes.
3. **Focus management is hard.** Typing goes to whatever window is focused. Always verify focus before text input.
4. **OpenRouter credits go fast.** 50 API calls = ~$2-3. For development, use local models for planning.
5. **Portal screenshots are annoying.** The notification sound + flash every capture is disruptive. Need silent capture.
6. **Task completion detection needs work.** Checking audio playback is not enough — need UI element detection ("Pause" button = playing).

---

## Commits Today

- `74e4687` — feat: vision-first hybrid agent architecture
- `30a7b67` — feat: full cloud agent with OpenRouter vision + planning
- `6ff1be1` — feat: improved cloud agent with real verifier and shell support
- `21a1d15` — fix: OpenRouter vision retry logic with smaller screenshot fallback

---

## Next Session Priority

1. ⭐ **Switch planning to local Ollama** (llama3.2:1b) — reduce API costs
2. ⭐ **Implement silent screenshot capture** — ffmpeg x11grab or kmsgrab
3. Fix window focus before typing
4. Better task completion detection (check for "Pause" button, URL bar)
5. Test with Brave already open (no shell needed)