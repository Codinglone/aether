#!/usr/bin/env python3
"""
Detect existing YouTube video in Brave and make it fullscreen.

1. Find running Brave browser
2. Focus the Brave window (multiple methods)
3. Maximize if needed
4. Press 'f' to toggle YouTube fullscreen
"""

import os
import subprocess
import time

from aether.action.linux import LinuxActionAdapter


def is_process_running(name: str) -> bool:
    """Check if a process is running by name."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", name],
            capture_output=True, text=True, check=False
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except Exception:
        return False


def focus_brave_window(action: LinuxActionAdapter) -> bool:
    """Try multiple methods to focus the Brave browser window."""
    
    # Method 1: Try using gtk-launch to activate (correct desktop file name)
    print("   Method 1: gtk-launch brave-browser...")
    for desktop_name in ["brave-browser", "brave-browser-beta", "com.brave.Browser"]:
        try:
            result = subprocess.run(
                ["gtk-launch", desktop_name],
                capture_output=True, text=True, check=False, timeout=3
            )
            if "no such application" not in result.stderr.lower():
                time.sleep(1)
                return True
        except Exception:
            pass
    
    # Method 2: Try running brave command (often brings existing window to front)
    print("   Method 2: brave --activate...")
    try:
        subprocess.Popen(
            ["brave", "--activate"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(1)
        return True
    except Exception:
        pass
    
    # Method 3: Use xdotool if available (unlikely on Wayland)
    print("   Method 3: xdotool...")
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "Brave"],
            capture_output=True, text=True, check=False, timeout=2
        )
        if result.stdout.strip():
            window_id = result.stdout.strip().split("\n")[0]
            subprocess.run(["xdotool", "windowactivate", window_id], check=False, timeout=2)
            time.sleep(0.5)
            return True
    except Exception:
        pass
    
    # Method 4: Use python-xlib to find and raise window
    print("   Method 4: python-xlib...")
    try:
        from Xlib.display import Display
        d = Display()
        root = d.screen().root
        
        def search_window(window, name):
            try:
                wm_name = window.get_wm_name()
                if wm_name and name.lower() in str(wm_name).lower():
                    return window
            except:
                pass
            try:
                for child in window.query_tree().children:
                    found = search_window(child, name)
                    if found:
                        return found
            except:
                pass
            return None
        
        target = search_window(root, "Brave")
        if target:
            from Xlib import X
            target.configure(stack_mode=X.Above)
            d.sync()
            d.set_input_focus(target, X.RevertToParent, X.CurrentTime)
            d.sync()
            time.sleep(0.5)
            return True
    except Exception:
        pass
    
    # Method 5: Use ydotool to Alt+Tab until Brave is focused
    print("   Method 5: Alt+Tab cycling...")
    env = os.environ.copy()
    if action._ydotool_socket:
        env["YDOTOOL_SOCKET"] = action._ydotool_socket
    
    for i in range(8):
        try:
            subprocess.run(
                ["ydotool", "key", "125:1", "15:1", "15:0", "125:0"],
                capture_output=True, env=env, check=False, timeout=2
            )
            time.sleep(0.4)
        except Exception:
            pass
    
    return False


def main():
    print("=" * 70)
    print("🎬 AETHER-NATIVE: YouTube Fullscreen (Detect Existing)")
    print("=" * 70)
    
    action = LinuxActionAdapter()
    
    # Check if Brave is running
    print("\n🔍 Checking if Brave is running...")
    if not is_process_running("brave"):
        print("❌ Brave is not running. Please open Brave with a YouTube video first.")
        print("   Example: brave https://www.youtube.com/watch?v=aqz-KE-bpKQ")
        return
    
    print("   ✅ Brave is running")
    
    # Focus the Brave window
    print("\n🎯 Focusing Brave window...")
    focused = focus_brave_window(action)
    
    if focused:
        print("   ✅ Window focused")
    else:
        print("   ⚠️  Could not confirm focus, continuing anyway...")
    
    time.sleep(1)
    
    # Maximize window (Super+Up in GNOME)
    print("\n🔲 Maximizing window (Super+Up)...")
    action.hotkey(["super"], "Up")
    time.sleep(0.5)
    
    # Click center of screen to ensure video player has focus
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
    
    center_x, center_y = screen_w // 2, int(screen_h * 0.55)
    print(f"\n🖱️  Clicking video area ({center_x}, {center_y})...")
    action.click(center_x, center_y)
    time.sleep(0.5)
    
    # Press 'f' to toggle YouTube fullscreen
    print("\n⛶  Toggling fullscreen (YouTube 'f' shortcut)...")
    action.type_text("f")
    time.sleep(0.5)
    
    print("\n   ✅ Done! YouTube should now be fullscreen.")
    print("   Press 'f' or ESC to exit fullscreen.")
    print("=" * 70)


if __name__ == "__main__":
    main()
