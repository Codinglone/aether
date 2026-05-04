#!/usr/bin/env python3
"""
Standalone mouse cursor control demo for Aether-Native.

Tests mouse movement and clicking using the best available backend:
- ydotool (Wayland)
- X11/python-xlib (X11/XWayland)
"""

import os
import time

from aether.action.linux import LinuxActionAdapter


def main():
    print("=" * 70)
    print("AETHER-NATIVE: Mouse Cursor Control Demo")
    print("=" * 70)
    
    action = LinuxActionAdapter()
    
    # Show which backend is being used
    if action._ydotool_socket:
        print(f"\n🖱️  Backend: ydotool (Wayland)")
        print(f"   Socket: {action._ydotool_socket}")
    elif action._display:
        print(f"\n🖱️  Backend: X11 (python-xlib)")
    else:
        print("\n❌ No input backend available!")
        print("   Install ydotool + start ydotoold for Wayland")
        print("   Or ensure X11/XWayland is available")
        return
    
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
    print(f"\n   Moving mouse in 3 seconds...")
    time.sleep(3)
    
    # Move mouse in a square pattern
    center_x, center_y = screen_w // 2, screen_h // 2
    offset = 150
    positions = [
        (center_x - offset, center_y - offset, "top-left"),
        (center_x + offset, center_y - offset, "top-right"),
        (center_x + offset, center_y + offset, "bottom-right"),
        (center_x - offset, center_y + offset, "bottom-left"),
        (center_x, center_y, "center (click)"),
    ]
    
    print("   Moving mouse...")
    for x, y, label in positions:
        print(f"      → {label} ({x}, {y})")
        action.click(x, y)
        time.sleep(0.6)
    
    print("\n   ✅ Mouse demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
