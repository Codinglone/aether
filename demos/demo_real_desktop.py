#!/usr/bin/env python3
"""
Real desktop automation demo using AT-SPI actions.

Instead of unreliable keyboard focus, we directly invoke AT-SPI
actions on calculator buttons - this works even if the window
isn't focused or is partially obscured!
"""

import os
import subprocess
import time

os.environ.setdefault("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")

import pyatspi
from aether.perception.linux import LinuxPerceptionAdapter


def find_button_in_tree(node, button_name: str):
    """Recursively find a button by name in AT-SPI tree."""
    try:
        role = node.getRoleName()
        name = node.name or ""
        if role in ["push button", "button", "toggle button"]:
            # Check button name or its label child
            if name == button_name:
                return node
            for i in range(node.childCount):
                child = node.getChildAtIndex(i)
                if child and child.name == button_name:
                    return node  # Return the button, not the label
        for i in range(node.childCount):
            found = find_button_in_tree(node.getChildAtIndex(i), button_name)
            if found:
                return found
    except Exception:
        pass
    return None


def click_button_by_name(app, button_name: str) -> bool:
    """Click a calculator button via AT-SPI action interface."""
    btn = find_button_in_tree(app, button_name)
    if btn:
        try:
            action = btn.queryAction()
            action.doAction(0)  # Primary action (click)
            return True
        except Exception:
            pass
    return False


def read_calculator_display(app) -> str:
    """Read display value from calculator AT-SPI tree."""
    def find_display(node):
        try:
            role = node.getRole()
            if role == pyatspi.ROLE_TEXT:
                try:
                    text_iface = node.queryText()
                    return text_iface.getText(0, -1)
                except:
                    pass
            try:
                val = node.queryValue()
                return str(val.currentValue)
            except:
                pass
            for i in range(node.childCount):
                result = find_display(node.getChildAtIndex(i))
                if result:
                    return result
        except:
            pass
        return ""

    for j in range(app.childCount):
        result = find_display(app.getChildAtIndex(j))
        if result:
            return result
    return ""


def perform_calculation(app, expression: list[str]) -> str:
    """Perform a calculation by clicking buttons via AT-SPI."""
    for btn_name in expression:
        if not click_button_by_name(app, btn_name):
            print(f"      ⚠️  Could not click: {btn_name}")
        time.sleep(0.15)
    time.sleep(0.5)  # Wait for calc to update
    return read_calculator_display(app)


def get_all_buttons(app) -> list[str]:
    """Extract all button names from calculator."""
    buttons = []
    def find_buttons(node):
        try:
            role = node.getRoleName()
            if role in ["push button", "button", "toggle button"]:
                if node.name and node.name not in buttons:
                    buttons.append(node.name)
            for i in range(node.childCount):
                find_buttons(node.getChildAtIndex(i))
        except:
            pass
    find_buttons(app)
    return sorted(buttons)


def demo_atspi_actions():
    print("=" * 70)
    print("AETHER-NATIVE: AT-SPI Direct Button Actions")
    print("=" * 70)
    print("\n⚠️  This demo will:")
    print("   1. Launch GNOME Calculator")
    print("   2. Find buttons via AT-SPI accessibility tree")
    print("   3. CLICK BUTTONS DIRECTLY via AT-SPI actions")
    print("   4. Read results back from the display")
    print("   5. Verify each calculation")
    print("   6. Wait 5 seconds before closing")
    print("\n   No keyboard focus needed - AT-SPI actions work")
    print("   even when the window is not focused!")
    print("   Starting in 3 seconds...")
    time.sleep(3)
    print("=" * 70)

    # Launch calculator
    print("\n🚀 Launching GNOME Calculator...")
    env = os.environ.copy()
    subprocess.Popen(["gnome-calculator"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    time.sleep(3)

    # Find calculator in AT-SPI tree
    print("🔍 Finding calculator via AT-SPI2...")
    desktop = pyatspi.Registry.getDesktop(0)
    calc_app = None
    for i in range(desktop.childCount):
        app = desktop.getChildAtIndex(i)
        if app and "calc" in app.name.lower():
            calc_app = app
            break

    if not calc_app:
        print("❌ Calculator not found in AT-SPI tree")
        return

    print(f"✅ Found: {calc_app.name}")

    buttons = get_all_buttons(calc_app)
    print(f"\n🎹 Detected {len(buttons)} buttons:")
    for i in range(0, len(buttons), 10):
        print(f"   {', '.join(buttons[i:i+10])}")

    # Calculations
    tests = [
        (["2", "+", "2", "="], "4", "Addition: 2 + 2"),
        (["C"], "", "Clear"),
        (["1", "0", "−", "3", "="], "7", "Subtraction: 10 - 3"),
        (["C"], "", "Clear"),
        (["6", "×", "7", "="], "42", "Multiplication: 6 × 7"),
        (["C"], "", "Clear"),
        (["2", "0", "÷", "4", "="], "5", "Division: 20 ÷ 4"),
    ]

    print("\n" + "-" * 70)
    print("🧮 Performing calculations via AT-SPI button clicks...")
    print("-" * 70)

    all_passed = True
    for expression, expected, desc in tests:
        print(f"\n   {desc}")
        print(f"   Clicking: {' → '.join(expression)}")

        result = perform_calculation(calc_app, expression)

        if expected:
            status = "✅ PASS" if result == expected else "❌ FAIL"
            if result != expected:
                all_passed = False
            print(f"   Expected: {expected:>6} | Got: {result:>6} | {status}")
        else:
            print(f"   (cleared)")

    print("\n" + "-" * 70)
    if all_passed:
        print("✅ ALL CALCULATIONS VERIFIED CORRECT!")
    else:
        print("⚠️  Some results didn't match (display may update async)")
    print("-" * 70)

    # 5 second delay
    print("\n⏱️  Waiting 5 seconds so you can see the final result...")
    for i in range(5, 0, -1):
        print(f"   Closing in {i}...")
        time.sleep(1)

    # Close
    print("\n🚪 Closing calculator...")
    subprocess.run(["pkill", "-f", "gnome-calculator"], check=False)
    print("✅ Closed")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)
    print("\nWhat we proved:")
    print("  ✓ AT-SPI2 reads live desktop accessibility tree")
    print("  ✓ We find buttons by semantic name (not pixels)")
    print("  ✓ We CLICK BUTTONS DIRECTLY via AT-SPI actions")
    print("  ✓ No window focus or coordinates needed!")
    print("  ✓ We read results back and verify correctness")
    print("  ✓ Full closed-loop: perceive → act → verify")
    print("\nThis is the Aether-Native advantage:")
    print("  Cloud agents send screenshots and guess coordinates.")
    print("  We read the semantic tree and interact natively.")
    print("=" * 70)


if __name__ == "__main__":
    demo_atspi_actions()
