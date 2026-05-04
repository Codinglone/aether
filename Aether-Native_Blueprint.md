# Aether-Native: Project Blueprint
**Version:** 1.0 (Targeting Fedora 43 / Wayland)
**Objective:** To build a Linux-native computer-use agent that eliminates the latency and precision issues of cloud-based vision models by leveraging OS-level accessibility trees and local inference.

---

## 1. The RALPH Loop Framework
To allow an agent to "one-shot" this or maintain it autonomously, we utilize the **RALPH (Reasoning, Action, Learning, Progress, History)** loop.

* **Reasoning:** Analyze the current UI state (AT-SPI Tree) vs. the user goal.
* **Action:** Execute specific D-Bus/libei input commands.
* **Learning:** Update `knowledge.md` with UI quirks (e.g., "The 'Save' button in App X doesn't fire AT-SPI events; use Vision").
* **Progress:** Track sub-task completion in `progress.json`.
* **History:** Log action sequences to avoid repeating failed paths.

---

## 2. Architecture Document (High-Level)
Aether-Native is designed as a **Local-First Hybrid Agent**. Unlike existing tools that rely solely on sending full-resolution screenshots to a cloud VLM (Vision Language Model), Aether-Native treats the Operating System as a structured data source.

### 2.1 Hybrid Perception System
The core innovation is the separation of "seeing" into two distinct channels:
* **Structural Channel (Primary):** Queries the `AT-SPI2` (Accessibility Bus) to retrieve a text-based tree of all UI elements. This provides 100% accurate coordinates without visual inference.
* **Visual Channel (Auxiliary):** Uses `PipeWire` to stream screen data only when necessary—such as interpreting complex canvas elements or verifying animations.

### 2.2 The Controller Loop
The system operates on the **Observer-Reason-Act** pattern, running entirely within the local user session.

```text
[OS UI State (AT-SPI)] -> [Minified Markdown] -> [Local VLM (Qwen2.5-VL)]
                                                      |
[Action Sequence (JSON)] <- [Reasoning / Task Planning]
      |
[D-Bus Input Injection] -> [Wayland Compositor (Mutter)]
```

---

## 3. Design Document (Component Details)
The design focuses on modularity, allowing the "Brain" to be swapped while keeping the "Hands" (input) and "Eyes" (perception) stable.

### 3.1 Perception Module (`at-spi-scraper`)
This module acts as the translator. It converts the massive D-Bus XML tree into a **Semantic UI Map**.
* **Target:** `org.a11y.Bus`
* **Functionality:** Recursively walk the accessibility tree. Filter out invisible nodes.
* **Output:** A compressed Markdown snippet (e.g., `[42] Button: "Submit" (x:400, y:300)`).

### 3.2 Execution Module (`mutter-remote-driver`)
Since Fedora 43 is Wayland-only, this module implements the **GNOME Remote Desktop D-Bus** interface.
* **Path:** `/org/gnome/Mutter/RemoteDesktop`
* **Methods:**
    * `NotifyPointerMotion(x, y)`: Moves the virtual mouse.
    * `NotifyPointerButton(button, state)`: Simulates clicks.
    * `NotifyKeyboardKeysym(keysym, state)`: Injects low-level keyboard events.

### 3.3 Reasoning Module (`vlm-bridge`)
Uses a **Local Inference Engine** to process tasks.
* **Model:** **Qwen2.5-VL-7B** (Quantized GGUF/Vulkan).
* **Backend:** `llama.cpp` targeting the integrated/dedicated GPU.

---

## 4. Implementation Document (Technical Stack)
| Component | Technology | Reasoning |
| :--- | :--- | :--- |
| **Language** | Rust 1.80+ | Memory safety + `zbus` abstractions. |
| **Input Injection** | `libei` + Mutter D-Bus | Modern Wayland standard for Fedora 43. |
| **Video Stream** | `pipewire-rs` | Direct access to the compositor frame buffer. |
| **Inference** | `llama.cpp` (Vulkan) | Local execution, no cloud latency. |

### 4.1 Folder Structure
```text
aether-native/
├── src/
│   ├── main.rs          # Main RALPH Loop execution logic
│   ├── perception/      # AT-SPI tree walking and PipeWire stream
│   ├── execution/       # D-Bus Remote Desktop proxy calls
│   └── brain/           # Local VLM connector / Prompt templates
├── proto/               # API definitions for structured tool-use
├── tests/               # Integration tests (using nested Mutter)
└── knowledge.md         # Long-term agent memory of UI behaviors
```

---

## 5. Requirements & Testing

### 5.1 Functional Requirements
* **FR1:** Agent must locate and click elements in the AT-SPI tree with >98% accuracy.
* **FR2:** Loop latency (Observation to Action) must be < 800ms.
* **FR3:** Must support multi-step macros (e.g., terminal commands followed by UI interaction).

### 5.2 Testing Strategy
1.  **The "Nested" Test:** Launch `mutter --nested`. The agent must navigate the inner window without affecting the host desktop.
2.  **Coordinate Accuracy:** Click a 1px target verified by focus-change events.
3.  **Self-Correction:** Simulate a button click failure; agent must recognize the lack of state change and retry using an alternative method (e.g., hotkeys).

---

## 6. Evaluation Framework
Success is measured by the **ALR Score (Action-Latency-Reliability)**:

$$ALR = (Success Rate \times 100) / Latency Seconds$$

### Comparison Metrics:
| Metric | Perplexity / Claude | Aether-Native |
| :--- | :--- | :--- |
| **Latency** | 3.5s - 6s | **0.4s - 0.8s** |
| **Grounding** | Pixel-based (Drift) | **OS-Tree (Precise)** |
| **Privacy** | Cloud-transmitted | **On-Device (Local)** |

---
**Note for Agent Initialization:** Start development with the `at-spi-scraper` module. Once the text-based UI tree is correctly parsed into Markdown, the mapping to coordinates becomes a trivial task for the local VLM.
