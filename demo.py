#!/usr/bin/env python3
"""Demo script showing Aether-Native RALPH loop in action."""

from pathlib import Path
from aether.core.loop import RalphLoop
from aether.core.brain import StubBrain
from aether.core.safety import SafetyChecker
from aether.core.verify import Verifier
from aether.core.memory import SessionMemory
from tests.harness import MockPerceptionAdapter, MockActionAdapter


def main():
    print("=" * 60)
    print("AETHER-NATIVE: Phase 0 MVP Demo")
    print("=" * 60)

    # Load the calculator fixture
    fixture = Path("tests/fixtures/calculator_linux.json")
    
    # Use a fresh adapter just for display
    display_perception = MockPerceptionAdapter(fixture)
    print(f"\n[1] Initial UI state:")
    uimap = display_perception.capture()
    for elem in uimap.elements:
        print(f"    - {elem.role}: '{elem.name}' at ({elem.bounds.x}, {elem.bounds.y})")
        for child in elem.children:
            print(f"      -> {child.role}: '{child.name}'")

    # Fresh components for the loop
    perception = MockPerceptionAdapter(fixture)
    action = MockActionAdapter()
    brain = StubBrain()
    memory = SessionMemory()
    verifier = Verifier()
    safety = SafetyChecker()

    loop = RalphLoop(perception, brain, action, memory, verifier, safety)

    print(f"\n[2] Submitting task: 'Click the 2 button'")
    result = loop.run("Click the 2 button")

    print(f"\n[3] Result: {result.status.upper()}")
    print(f"    Actions taken: {result.actions_taken}")
    print(f"    Final state: {loop.state.value}")

    print(f"\n[4] Executed actions:")
    for i, a in enumerate(action.executed_actions, 1):
        print(f"    {i}. {a['type'].upper()} -> x={a['x']}, y={a['y']}")

    print(f"\n[5] Session memory:")
    print(f"    History entries: {len(memory.history)}")
    print(f"    Current task: {memory.progress.current_task}")
    print(f"    Done: {memory.progress.done}")

    # Show post-click state
    print(f"\n[6] Final UI state:")
    final_uimap = perception.capture()
    for elem in final_uimap.elements:
        for child in elem.children:
            print(f"      -> {child.role}: '{child.name}'")

    print("\n" + "=" * 60)
    if result.status == "success":
        print("SUCCESS! The RALPH loop:")
        print("  - Scraped the UI state from the accessibility tree")
        print("  - Reasoned about which element to click")
        print("  - Executed the click action")
        print("  - Verified the state changed (display: 0 -> 2)")
    else:
        print(f"Result: {result.status} - {result.reason}")
    print("=" * 60)


if __name__ == "__main__":
    main()
