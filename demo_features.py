#!/usr/bin/env python3
"""Demo: Self-healing macros and safety check."""

from pathlib import Path
from aether.core.models import Action
from aether.macro.recorder import MacroRecorder
from aether.macro.player import MacroPlayer
from aether.core.safety import SafetyChecker
from tests.harness import MockPerceptionAdapter, MockActionAdapter


def demo_macros():
    print("=" * 60)
    print("SELF-HEALING MACROS DEMO")
    print("=" * 60)

    # Record a macro
    recorder = MacroRecorder()
    recorder.start_recording("Click calculator button")
    
    action = Action(
        type="click",
        params={"x": 100, "y": 200},
        reason="Click the 2 button",
        expected_change="Display updates",
    )
    recorder.record_action(action, element_name="2", element_role="push button")
    macro = recorder.stop_recording()

    print(f"\n[1] Recorded macro: '{macro.name}'")
    print(f"    Intent: click '{macro.intents[0].target.name}' ({macro.intents[0].target.role})")

    # Replay on same UI
    fixture = Path("tests/fixtures/calculator_linux.json")
    perception = MockPerceptionAdapter(fixture)
    action_adapter = MockActionAdapter()
    player = MacroPlayer(perception, action_adapter)

    print(f"\n[2] Replaying macro on original UI...")
    player.play(macro)
    print(f"    Executed: {len(action_adapter.executed_actions)} action(s)")

    # Self-healing: change the name, keep the role
    print(f"\n[3] Self-healing demo:")
    print(f"    Macro targets: name='2', role='push button'")
    print(f"    But UI now has button named 'NonExistent'...")
    
    macro.intents[0].target.name = "NonExistent"
    action_adapter.clear()
    
    player.play(macro)
    print(f"    Still executed: {len(action_adapter.executed_actions)} action(s)")
    print(f"    -> Fallback found element by role='push button'")


def demo_safety():
    print("\n" + "=" * 60)
    print("SAFETY CHECKER DEMO")
    print("=" * 60)

    safety = SafetyChecker()

    # Safe action
    safe = Action(
        type="click",
        params={"x": 100, "y": 200},
        reason="test",
        expected_change="test",
    )
    is_safe, err = safety.check(safe)
    print(f"\n[1] Click(100, 200): {'ALLOWED' if is_safe else 'BLOCKED'}")

    # Dangerous action
    dangerous = Action(
        type="shell",
        params={"command": "rm -rf /"},
        reason="evil",
        expected_change="evil",
    )
    is_safe, err = safety.check(dangerous)
    print(f"[2] Shell('rm -rf /'): {'ALLOWED' if is_safe else 'BLOCKED'} - {err}")

    # Out of bounds
    oob = Action(
        type="click",
        params={"x": 99999, "y": 100},
        reason="test",
        expected_change="test",
    )
    is_safe, err = safety.check(oob)
    print(f"[3] Click(99999, 100): {'ALLOWED' if is_safe else 'BLOCKED'} - {err}")


if __name__ == "__main__":
    demo_macros()
    demo_safety()
    print("\n" + "=" * 60)
    print("All demos complete!")
    print("=" * 60)
