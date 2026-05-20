#!/usr/bin/env python3
"""
YouTube fullscreen demo using mouse and keyboard.

Opens Brave browser, navigates to a YouTube video, clicks to focus,
then maximizes the video to fullscreen using the YouTube 'f' shortcut.
"""

import os
import subprocess
import time

from aether.action.linux import LinuxActionAdapter


def main():
    print("=" * 70)
    print("🎬 AETHER-NATIVE: YouTube Fullscreen Demo")
    print("=" * 70)
    print("\n   Opens Brave → YouTube → Clicks video → Fullscreen")
    print("\n   ⚠️  Make sure you're not using the mouse/keyboard!")
    print("   Starting in 3 seconds...")
    time.sleep(3)

    action = LinuxActionAdapter()

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

    print(f"\n   Screen: {screen_w}x{screen_h}")

    # Launch Brave with YouTube (Big Buck Bunny - open source, short)
    video_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    print(f"\n🚀 Launching Brave with YouTube...")
    print(f"   URL: {video_url}")
    
    subprocess.Popen(
        ["brave", "--new-window", video_url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for browser to open and page to load
    print("   Waiting for page to load...")
    time.sleep(6)

    # Handle any permission dialogs (screen sharing, etc.)
    print("   Checking for permission dialogs...")
    _handle_permission_dialogs()

    # Maximize browser window using keyboard shortcut (Super+Up in GNOME)
    print("\n🔲 Maximizing browser window (Super+Up)...")
    action.hotkey(["super"], "Up")
    time.sleep(1)

    # Click on the center of the screen where the video should be
    # This both focuses the page and starts playback
    center_x, center_y = screen_w // 2, int(screen_h * 0.55)
    print(f"\n🖱️  Clicking video area ({center_x}, {center_y})...")
    action.click(center_x, center_y)
    time.sleep(1)

    # Try clicking the fullscreen button location (bottom-right of video)
    # YouTube fullscreen button is roughly at 96% width, 92% height of player
    fs_x = int(screen_w * 0.96)
    fs_y = int(screen_h * 0.88)
    print(f"\n⛶  Clicking fullscreen button ({fs_x}, {fs_y})...")
    action.click(fs_x, fs_y)
    time.sleep(1)

    # Fallback: use YouTube 'f' keyboard shortcut (most reliable)
    print("   Pressing 'f' key (YouTube fullscreen shortcut)...")
    action.type_text("f")
    time.sleep(0.5)

    print("\n   ✅ YouTube should now be fullscreen!")
    print("   Press ESC to exit fullscreen when done watching.")
    print("=" * 70)


def _handle_permission_dialogs():
    """Quick permission dialog handler for this demo."""
    import pyatspi
    
    dialog_titles = ["share", "permission", "allow", "screen"]
    allow_buttons = ["allow", "share", "yes", "ok", "accept"]
    
    desktop = pyatspi.Registry.getDesktop(0)
    for i in range(desktop.childCount):
        app = desktop.getChildAtIndex(i)
        if not app or not app.name:
            continue
        
        app_name_lower = app.name.lower()
        if any(title in app_name_lower for title in dialog_titles):
            print(f"   🛡️  Detected dialog: '{app.name}'")
            
            # Try to find and click allow button
            def find_button(node, name):
                try:
                    if node.getRoleName() == "push button" and name.lower() in (node.name or "").lower():
                        return node
                    for j in range(node.childCount):
                        found = find_button(node.getChildAtIndex(j), name)
                        if found:
                            return found
                except:
                    pass
                return None
            
            for btn_name in allow_buttons:
                btn = find_button(app, btn_name)
                if btn:
                    try:
                        btn.queryAction().doAction(0)
                        print(f"   ✅ Clicked '{btn_name}'")
                        time.sleep(0.5)
                        return
                    except:
                        pass


if __name__ == "__main__":
    main()
