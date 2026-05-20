#!/usr/bin/env python3
"""
YouTube fullscreen using mouse cursor with slow visible movement.

1. Detects existing Brave with YouTube
2. Moves mouse SLOWLY to the fullscreen button so you can see it
3. Clicks
"""

import os
import subprocess
import time

from aether.action.linux import LinuxActionAdapter


def is_process_running(name: str) -> bool:
    try:
        result = subprocess.run(
            ["pgrep", "-f", name],
            capture_output=True, text=True, check=False
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except Exception:
        return False


def main():
    print("=" * 70)
    print("🎬 YouTube Fullscreen - Slow Mouse Demo")
    print("=" * 70)
    print("\n   The mouse will move SLOWLY so you can see where it goes.")
    print("   Tell me if the clicks are in the right place!")

    action = LinuxActionAdapter()

    # Check Brave is running
    print("\n🔍 Checking Brave...")
    if not is_process_running("brave"):
        print("❌ Brave not running. Open Brave with YouTube first.")
        return
    print("   ✅ Brave is running")

    # Get screen size
    try:
        import gi
        gi.require_version('Gdk', '4.0')
        from gi.repository import Gdk
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geometry = monitor.get_geometry()
        screen_w, screen_h = geometry.width, geometry.height
    except Exception:
        screen_w, screen_h = 1920, 1080

    print(f"   Screen: {screen_w}x{screen_h}")

    # Step 1: Move to center of screen (assumes Brave is main window)
    center_x, center_y = screen_w // 2, int(screen_h * 0.5)
    print(f"\n🖱️  Step 1: Moving to center ({center_x}, {center_y}) - watching...")
    action.move_mouse(center_x, center_y, duration=1.5)
    time.sleep(0.3)
    print("   → Clicking to focus Brave")
    action.click(center_x, center_y)
    time.sleep(0.5)

    # Step 2: Move to video area center
    video_y = int(screen_h * 0.55)
    print(f"\n🖱️  Step 2: Moving to video ({center_x}, {video_y}) - watching...")
    action.move_mouse(center_x, video_y, duration=1.0)
    time.sleep(0.3)
    print("   → Clicking to play/pause")
    action.click(center_x, video_y)
    time.sleep(0.5)

    # Step 3: Move to fullscreen button (bottom-right of player)
    # YouTube fullscreen icon is typically near bottom-right corner
    fs_x = screen_w - 50
    fs_y = screen_h - 100
    print(f"\n🖱️  Step 3: Moving to fullscreen button ({fs_x}, {fs_y}) - watching...")
    print("   → Look at the bottom-right of the YouTube player!")
    action.move_mouse(fs_x, fs_y, duration=1.5)
    time.sleep(0.3)
    print("   → Clicking fullscreen button")
    action.click(fs_x, fs_y)
    time.sleep(0.5)

    print("\n" + "=" * 70)
    print("   ✅ Mouse moved and clicked fullscreen button.")
    print("   Did it click the right place?")
    print("   If not, tell me the correct coordinates and I'll adjust.")
    print("=" * 70)


if __name__ == "__main__":
    main()
