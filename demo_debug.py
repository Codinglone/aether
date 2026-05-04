#!/usr/bin/env python3
"""Debug demo script showing Aether-Native RALPH loop internals."""

from pathlib import Path
from aether.core.loop import RalphLoop
from aether.core.brain import StubBrain
from aether.core.safety import SafetyChecker
from aether.core.verify import Verifier
from aether.core.memory import SessionMemory
from tests.harness import MockPerceptionAdapter, MockActionAdapter


def main():
    print("=" * 60)
    print("AETHER-NATIVE: Debug Demo")
    print("=" * 60)

    fixture = Path("tests/fixtures/calculator_linux.json")
    perception = MockPerceptionAdapter(fixture)
    action = MockActionAdapter()
    brain = StubBrain()
    memory = SessionMemory()
    verifier = Verifier()
    safety = SafetyChecker()

    # Show initial state
    print("\n[INITIAL STATE]")
    uimap = perception.capture()
    for elem in uimap.elements:
        print(f"  Frame: {elem.name}")
        for child in elem.children:
            print(f"    -> {child.role}: '{child.name}' (id={child.id})")

    # Show state after transition
    print("\n[STATE AFTER TRANSITION]")
    uimap2 = perception.capture()
    for elem in uimap2.elements:
        for child in elem.children:
            print(f"    -> {child.role}: '{child.name}' (id={child.id})")

    # Verify the transition is detectable
    print("\n[VERIFICATION TEST]")
    result = verifier.verify(uimap, uimap2, None)
    print(f"  Success: {result.success}")
    print(f"  Strategy: {result.matched_strategy}")
    print(f"  Details: {result.details}")

    # Now run the full loop
    print("\n" + "=" * 60)
    print("[RUNNING RALPH LOOP]")
    print("=" * 60)

    # Reset for clean run
    perception = MockPerceptionAdapter(fixture)
    action = MockActionAdapter()
    loop = RalphLoop(perception, brain, action, memory, verifier, safety)

    result = loop.run("Click the 2 button")

    print(f"\nResult: {result.status.upper()}")
    print(f"Actions taken: {result.actions_taken}")
    print(f"Reason: {result.reason or 'N/A'}")

    print(f"\nExecuted actions:")
    for i, a in enumerate(action.executed_actions, 1):
        print(f"  {i}. {a}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
