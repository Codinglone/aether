#!/usr/bin/env python3
"""
Demo: Continuous video recording for silent screenshot capture.

This demo shows how ffmpeg continuous recording eliminates
GNOME portal notification sounds/flashes.
"""

import time

from aether.perception.video_recorder import VideoRecorder
from aether.perception.vision_first import VisionFirstPerceptionAdapter


def main():
    print("=" * 60)
    print("AETHER SILENT VIDEO CAPTURE DEMO")
    print("Uses ffmpeg background recording — no portal notifications!")
    print("=" * 60)

    # Start video recorder
    recorder = VideoRecorder(width=640, fps=0.5, quality=5)
    print("\n[1] Starting background ffmpeg recording...")
    recorder.start()

    # Wait a moment for frames to accumulate
    time.sleep(3)

    # Capture a few frames
    print("\n[2] Capturing frames from stream (should be instant and silent):")
    for i in range(5):
        start = time.time()
        frame_path = recorder.get_latest_frame(f"/tmp/stream_frame_{i}.jpg")
        elapsed = time.time() - start
        print(f"    Frame {i+1}: {frame_path} ({elapsed*1000:.0f}ms)")
        time.sleep(2)

    # Show stats
    print(f"\n[3] Recorder stats:")
    stats = recorder.get_stats()
    for k, v in stats.items():
        print(f"    {k}: {v}")

    # Analyze one frame with vision
    print(f"\n[4] Analyzing frame with vision model...")
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("ERROR: Set OPENROUTER_API_KEY environment variable")
        print("Get one at: https://openrouter.ai/settings/keys")
        return
    adapter = VisionFirstPerceptionAdapter(
        openrouter_api_key=api_key,
        openrouter_model="openai/gpt-4o-mini",
        vision_timeout=30,
        screenshot_scale=-1,  # Already sized
    )

    # Override to use our frame
    frame_path = recorder.get_latest_frame()
    adapter._capture_screenshot = lambda: frame_path

    start = time.time()
    ui_map = adapter.capture()
    elapsed = time.time() - start

    print(f"    Vision analysis in {elapsed:.1f}s")
    print(f"    App: {ui_map.active_window.name if ui_map.active_window else 'unknown'}")
    print(f"    Elements: {len(ui_map.elements)}")
    for elem in ui_map.elements[:5]:
        print(f"      - {elem.name} ({elem.role}) at ({elem.bounds.x}, {elem.bounds.y})")

    # Stop recorder
    print(f"\n[5] Stopping recorder...")
    recorder.stop()

    print(f"\n{'='*60}")
    print("Done! No notification sounds or flashes were triggered.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()