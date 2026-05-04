# Aether-Native Phase 1 Plan: Cross-Platform & Ghost Overlay

**Goal:** Expand beyond Linux to macOS and Windows, add visual feedback layer.
**Timeline:** 2-3 weeks
**Priority:** macOS first (similar accessibility model to AT-SPI), then Windows.

## 1. macOS Perception Adapter (`aether/perception/macos.py`)

**Technology:** `pyobjc-framework-ApplicationServices` (AXUIElement)
**Why:** macOS Accessibility API is mature, provides semantic trees similar to AT-SPI.

### Tasks
- [ ] Install `pyobjc` and `pyobjc-framework-ApplicationServices`
- [ ] Implement `MacOSPerceptionAdapter(BasePerceptionAdapter)`
- [ ] Map AX roles to generic Aether roles:
  - `AXButton` → `push button`
  - `AXTextField` → `text`
  - `AXWindow` → `frame`
  - `AXStaticText` → `label`
- [ ] Implement `capture_state()` using `AXUIElementCreateApplication()` + `AXUIElementCopyAttributeValue()`
- [ ] Implement `find_element()` with recursive tree walking
- [ ] Handle macOS permission dialog (`kAXTrustedCheckOptionPrompt`)
- [ ] Add tests with mocked AXUIElement (or skip on non-macOS CI)

### Key Differences from Linux
- macOS requires explicit accessibility permissions (System Preferences → Security → Accessibility)
- Role names are prefixed with `AX` (e.g., `AXButton` vs `push button`)
- No DBus, uses CoreFoundation runloop

## 2. Windows Perception Adapter (`aether/perception/windows.py`)

**Technology:** `pywinauto` or `comtypes` + `UIAutomationCore.dll`
**Why:** Windows UI Automation (UIA) is the modern standard, replacing MSAA.

### Tasks
- [ ] Evaluate `pywinauto` vs raw `comtypes` UIA approach
  - `pywinauto`: Higher-level, easier to use, but heavier dependency
  - `comtypes`: Lower-level, more control, lighter weight
  - **Decision:** Start with `pywinauto` for speed, migrate to `comtypes` if needed
- [ ] Implement `WindowsPerceptionAdapter(BasePerceptionAdapter)`
- [ ] Map UIA control types to generic Aether roles:
  - `UIA_ButtonControlTypeId` → `push button`
  - `UIA_EditControlTypeId` → `text`
  - `UIA_WindowControlTypeId` → `frame`
- [ ] Implement `capture_state()` using `Desktop(backend="uia")`
- [ ] Handle Windows permissions (run as admin not required for UIA)
- [ ] Add tests with mocked UIA elements

### Key Differences from Linux
- UIA uses `control_type` instead of `role`
- Window handles (HWND) instead of X11 window IDs
- No DBus equivalent, uses COM

## 3. Ghost Overlay (`aether/overlay/`)

**Goal:** Visual feedback showing what Aether is doing (bounding boxes, click highlights, action labels)
**Technology:** Platform-specific transparent windows

### Design
```
┌─────────────────────────────────────┐
│  [Ghost Overlay - always on top]    │
│  ┌──────────────┐                   │
│  │  🖱️ Click    │ ← Bounding box   │
│  │  "Submit"    │   + label        │
│  └──────────────┘                   │
│         ┌─────────────────────┐     │
│         │  📝 Type "hello"    │     │
│         └─────────────────────┘     │
└─────────────────────────────────────┘
```

### Tasks
- [ ] Linux: GTK3/4 transparent window with Cairo drawing (`gi.repository.Gtk`, `Gdk`)
- [ ] macOS: `NSWindow` with `NSWindowStyleMaskBorderless` + transparent background
- [ ] Windows: `WS_EX_LAYERED` + `WS_EX_TRANSPARENT` window with GDI+ drawing
- [ ] Draw bounding boxes around target elements (yellow = pending, green = success, red = error)
- [ ] Show action labels ("Click: Submit", "Type: hello@example.com")
- [ ] Auto-dismiss after action completes (2s fade-out)
- [ ] Configurable opacity and colors

### API
```python
class GhostOverlay:
    def highlight_element(self, bounds: tuple[int, int, int, int], label: str, color: str = "yellow")
    def show_action(self, action_type: str, target: str, status: str = "pending")
    def clear(self)
    def close(self)
```

## 4. PipeWire Screenshot Fallback (`aether/perception/screenshot.py`)

**Goal:** When AT-SPI/AX/UIA tree is empty or incomplete, fall back to screenshot + OCR
**Technology:** `pipewire` + `ffmpeg` (Linux), `screencapture` (macOS), `PIL.ImageGrab` (Windows)

### Tasks
- [ ] Linux: `pw-cat` or `ffmpeg -f pipewire` for screenshot
  - Alternative: `gnome-screenshot` or `grim` (Wayland)
  - Alternative: `xwd` (X11)
- [ ] macOS: `screencapture -x` (built-in, no deps)
- [ ] Windows: `PIL.ImageGrab.grab()` or `pygetwindow` + `pyautogui`
- [ ] Integrate with perception adapters: if `capture_state()` returns empty tree, trigger screenshot
- [ ] Optional: OCR with `easyocr` or `tesseract` to extract text from screenshot
- [ ] Cache screenshots to avoid repeated captures within 500ms

## 5. Cross-Platform Action Adapters

### macOS Action Adapter (`aether/action/macos.py`)
- [ ] `click(x, y)`: `CGEventCreateMouseEvent` + `CGEventPost`
- [ ] `type_text(text)`: `CGEventCreateKeyboardEvent` loop
- [ ] `hotkey(modifiers, key)`: `CGEventFlags` + key events
- [ ] `focus_window(title)`: `AXUIElementSetAttributeValue(kAXFrontmostAttribute)`

### Windows Action Adapter (`aether/action/windows.py`)
- [ ] `click(x, y)`: `win32api.mouse_event` or `SendInput`
- [ ] `type_text(text)`: `win32api.keybd_event` or `SendInput`
- [ ] `hotkey(modifiers, key)`: `SendInput` with `KEYBDINPUT` structs
- [ ] `focus_window(title)`: `win32gui.FindWindow` + `win32gui.SetForegroundWindow`

## 6. Unified Platform Detection

```python
# aether/platform.py
import sys

def get_platform() -> str:
    if sys.platform == "linux":
        return "linux"
    elif sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    raise RuntimeError(f"Unsupported platform: {sys.platform}")

def create_perception_adapter():
    platform = get_platform()
    if platform == "linux":
        from aether.perception.linux import LinuxPerceptionAdapter
        return LinuxPerceptionAdapter()
    elif platform == "macos":
        from aether.perception.macos import MacOSPerceptionAdapter
        return MacOSPerceptionAdapter()
    elif platform == "windows":
        from aether.perception.windows import WindowsPerceptionAdapter
        return WindowsPerceptionAdapter()

def create_action_adapter():
    # Similar pattern...
```

## 7. Test Strategy

- [ ] macOS tests: Mock `AXUIElement` using `unittest.mock` (skip integration tests on CI)
- [ ] Windows tests: Mock `pywinauto` / `comtypes` objects
- [ ] Overlay tests: Verify drawing commands are called with correct coordinates
- [ ] Screenshot tests: Mock `subprocess.run` for `screencapture`/`ffmpeg`
- [ ] Cross-platform: GitHub Actions matrix (ubuntu-latest, macos-latest, windows-latest)

## 8. Migration & Refactoring

- [ ] Extract `BasePerceptionAdapter` into `aether/perception/base.py` if not already
- [ ] Extract `BaseActionAdapter` into `aether/action/base.py`
- [ ] Move Linux-specific code to `aether/perception/linux.py` and `aether/action/linux.py`
- [ ] Update `__init__.py` files to expose platform-agnostic factory functions

## Task Breakdown (Estimated)

| # | Task | Est. Time | Owner |
|---|------|-----------|-------|
| 1 | macOS Perception Adapter | 3 days | TBD |
| 2 | macOS Action Adapter | 2 days | TBD |
| 3 | Windows Perception Adapter | 4 days | TBD |
| 4 | Windows Action Adapter | 2 days | TBD |
| 5 | Ghost Overlay (Linux) | 2 days | TBD |
| 6 | Ghost Overlay (macOS) | 1 day | TBD |
| 7 | Ghost Overlay (Windows) | 1 day | TBD |
| 8 | PipeWire Screenshot | 1 day | TBD |
| 9 | Unified Platform Detection | 0.5 day | TBD |
| 10 | Tests & CI Matrix | 2 days | TBD |
| | **Total** | **~18 days** | |

## Success Criteria

- [ ] `demo_multi_app.py` runs on macOS (Calculator → TextEdit → Finder)
- [ ] `demo_multi_app.py` runs on Windows (Calculator → Notepad → File Explorer)
- [ ] Ghost Overlay shows bounding boxes on all platforms
- [ ] Screenshot fallback works when accessibility APIs return empty trees
- [ ] All tests pass on Linux, macOS, Windows CI

## Notes

- **macOS permissions** are the biggest friction point. Users must manually grant accessibility permissions in System Preferences. Consider adding a setup wizard.
- **Windows UIA** is more reliable than MSAA but slower. Cache element trees when possible.
- **Ghost Overlay** should be optional (`--no-overlay` flag) for headless/remote usage.
- Keep Phase 1 focused on **adapters + overlay**. Don't add new AI models or complex reasoning yet.

---

## Phase 1.5: Vision & Brain Integration (Next 3 Tasks)

These tasks build on the completed hybrid perception system to add real intelligence.

### Task 11: Multimodal Vision Support (`ollama pull llava`)

**Goal:** Make the LLM fallback actually "see" screenshots instead of guessing.
**Current state:** `LocalLLM.analyze_screenshot()` reasons from text description only.
**Target:** Feed screenshot image to a vision model.

#### Subtasks
- [ ] `ollama pull llava` (or `bakllava`, `moondream`)
- [ ] Update `LocalLLM.analyze_screenshot()` to accept image bytes
- [ ] Use Ollama's `/api/generate` with `images` field (base64-encoded PNG)
- [ ] Prompt: "What UI elements do you see? Where is the [button/input]?"
- [ ] Parse response to extract: element_name, coordinates, confidence
- [ ] Benchmark: vision vs text-only accuracy on common UI patterns

#### Why This Matters
| | Text-Only LLM | Vision LLM |
|--|---------------|------------|
| Knows button exists? | Sometimes | Yes |
| Knows exact position? | No | Yes (pixels) |
| Handles custom UIs? | Poorly | Well |
| Speed | ~200ms | ~1-2s |

#### Files to Modify
- `aether/brain/local_llm.py` — Add `analyze_screenshot_vision()`
- `aether/perception/hybrid.py` — Use vision fallback when text fallback fails

---

### Task 12: Integrate Hybrid Perception into RALPH Loop

**Goal:** The brain (RALPH) should use hybrid perception for all decisions.
**Current state:** RALPH loop has hardcoded action sequences. No dynamic perception.
**Target:** RALPH queries perception before each action, adapts to UI changes.

#### Subtasks
- [ ] Inject `HybridPerceptionAdapter` into `RALPHLoop` constructor
- [ ] Before each action:
  1. `perception.capture()` — get current UI state
  2. `brain.suggest_action(task, elements, history)` — LLM decides next step
  3. `action.execute()` — perform the action
  4. `perception.verify()` — confirm UI changed as expected
- [ ] Add retry logic: if action fails, re-query perception and try alternative
- [ ] Handle "stuck" detection: if same state repeats 3x, trigger screenshot + vision
- [ ] Add `max_retries` and `timeout` to task execution

#### Example Flow
```
User: "Submit the form"
RALPH:
  1. capture() → [NameField, EmailField, SubmitButton]
  2. suggest_action() → {"action": "click", "target": "SubmitButton"}
  3. click("SubmitButton")
  4. capture() → [SuccessMessage] ✅
```

#### Files to Modify
- `aether/core/loop.py` — Wire in perception + brain
- `aether/core/brain.py` — Add `suggest_action()` method
- `demo_smart_task.py` — Demo: "Find and click X" with dynamic adaptation

---

### Task 13: Smart Task Demo — End-to-End Intelligence

**Goal:** A demo that proves the entire system works together dynamically.
**Current demos:** Static sequences (always click same buttons).
**Target:** Natural language task → dynamic perception → adaptive execution.

#### Demo Ideas
1. **"Play a YouTube video in Brave"**
   - Detect if Brave is running (AT-SPI or process check)
   - If not, launch it
   - Find YouTube tab or navigate to youtube.com
   - Find first video thumbnail (AT-SPI or vision)
   - Click it, wait for player, click fullscreen

2. **"Send a message in Discord"**
   - Detect Discord window (Electron, no AT-SPI)
   - Screenshot + vision fallback to find message input
   - Type message, find send button, click it

3. **"Open Settings and turn on Bluetooth"**
   - AT-SPI finds Settings app
   - Navigate to Bluetooth panel
   - Find toggle, check current state, toggle if needed
   - Verify state changed

#### Acceptance Criteria
- [ ] Task succeeds even if UI layout changes slightly
- [ ] Falls back to vision if AT-SPI returns empty tree
- [ ] Reports progress in real-time (console or overlay)
- [ ] Handles failures gracefully (retry, alternative action, or clear error)

#### Files to Create
- `demo_smart_youtube.py` — "Play YouTube video" end-to-end
- `demo_smart_settings.py` — "Toggle Bluetooth" with verification
- `demo_smart_discord.py` — "Send message" in Electron app

---

## Updated Task Breakdown

| # | Task | Est. Time | Status |
|---|------|-----------|--------|
| 1 | macOS Perception Adapter | 3 days | 🔲 Pending |
| 2 | macOS Action Adapter | 2 days | 🔲 Pending |
| 3 | Windows Perception Adapter | 4 days | 🔲 Pending |
| 4 | Windows Action Adapter | 2 days | 🔲 Pending |
| 5 | Ghost Overlay (Linux) | 2 days | 🔲 Pending |
| 6 | Ghost Overlay (macOS) | 1 day | 🔲 Pending |
| 7 | Ghost Overlay (Windows) | 1 day | 🔲 Pending |
| 8 | PipeWire Screenshot | 1 day | ✅ Done |
| 9 | Unified Platform Detection | 0.5 day | 🔲 Pending |
| 10 | Tests & CI Matrix | 2 days | 🔲 Pending |
| 11 | Multimodal Vision (llava) | 1 day | 🔲 **Next** |
| 12 | RALPH + Hybrid Integration | 2 days | 🔲 **Next** |
| 13 | Smart Task Demos | 2 days | 🔲 **Next** |
| | **Total** | **~23 days** | |

---

## What Was Completed Today

✅ **ydotool Wayland mouse support** — mouse now moves smoothly on Wayland  
✅ **ffmpeg screenshot backend** — captures desktop via XWayland  
✅ **LocalLLM via Ollama HTTP API** — `llama3.2:1b`, no cloud, ~200ms  
✅ **HybridPerceptionAdapter** — AT-SPI primary + screenshot/LLM fallback  
✅ **UIElement metadata** — supports fallback context (confidence, reasoning)  
✅ **Slow mouse animation** — visible cursor movement with `--absolute`  
✅ **4/5 demos passing** — Calculator, Settings, File Manager, Mouse Cursor  

**Next session focus:** Pick one of Tasks 11, 12, or 13 to implement.
