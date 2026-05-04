#!/usr/bin/env python3
"""
YouTube fullscreen using ONLY mouse cursor.

Detects existing Brave with YouTube, moves mouse to click on it,
then clicks the fullscreen button. No keyboard shortcuts used.
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
    print("🎬 YouTube Fullscreen - Mouse Only")
    print("=" * 70)

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

    # Step 1: Move to center of screen (assumes Brave is the main window)
    # and click to focus it
    center_x, center_y = screen_w // 2, int(screen_h * 0.5)
    print(f"\n🖱️  Step 1: Clicking center of screen ({center_x}, {center_y})")
    print("   → This should focus the Brave window")
    action.click(center_x, center_y)
    time.sleep(0.5)

    # Step 2: Click again slightly lower (video area center)
    video_y = int(screen_h * 0.55)
    print(f"\n🖱️  Step 2: Clicking video area ({center_x}, {video_y})")
    print("   → This starts/plays the video if paused")
    action.click(center_x, video_y)
    time.sleep(0.5)

    # Step 3: Move to fullscreen button location
    # YouTube fullscreen button is at bottom-right of player
    # Typical position: ~96% width, ~90% height
    fs_x = int(screen_w * 0.96)
    fs_y = int(screen_h * 0.90)
    print(f"\n🖱️  Step 3: Clicking fullscreen button ({fs_x}, {fs_y})")
    print("   → This should maximize the video")
    action.click(fs_x, fs_y)
    time.sleep(0.5)

    # Step 4: If that didn't work, try a few more positions nearby
    # YouTube's fullscreen icon might be slightly different position
    print("\n🖱️  Step 4: Trying alternate fullscreen positions...")
    alternates = [
        (int(screen_w * 0.95), int(screen_h * 0.92)),
        (int(screen_w * 0.97), int(screen_h * 0.88)),
        (screen_w - 50, screen_h - 80),
        (screen_w - 80, screen_h - 100),
    ]
    for x, y in alternates:
        print(f"   Trying ({x}, {y})...")
        action.click(x, y)
        time.sleep(0.3)

    print("\n   ✅ Done! YouTube fullscreen button should have been clicked.")
    print("=" * 70)


if __name__ == "__main__":
    main()
