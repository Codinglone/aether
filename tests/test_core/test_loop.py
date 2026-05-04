import pytest
from pathlib import Path

from aether.core.loop import RalphLoop, LoopState
from aether.core.brain import StubBrain
from aether.core.safety import SafetyChecker
from aether.core.verify import Verifier
from aether.core.memory import SessionMemory
from tests.harness import MockPerceptionAdapter, MockActionAdapter


class TestRalphLoop:
    def test_loop_completes_task(self):
        fixture = Path("tests/fixtures/calculator_linux.json")
        perception = MockPerceptionAdapter(fixture)
        action = MockActionAdapter()
        brain = StubBrain()
        memory = SessionMemory()
        verifier = Verifier()
        safety = SafetyChecker()

        loop = RalphLoop(perception, brain, action, memory, verifier, safety)
        result = loop.run("Click Save")

        assert result.status == "success"
        assert result.actions_taken >= 1

    def test_loop_state_transitions(self):
        fixture = Path("tests/fixtures/calculator_linux.json")
        perception = MockPerceptionAdapter(fixture)
        action = MockActionAdapter()
        brain = StubBrain()
        memory = SessionMemory()
        verifier = Verifier()
        safety = SafetyChecker()

        loop = RalphLoop(perception, brain, action, memory, verifier, safety)
        assert loop.state == LoopState.IDLE
        result = loop.run("test")
        assert loop.state == LoopState.IDLE

    def test_safety_aborts_on_unsafe(self):
        from aether.core.models import Action, ActionPlan

        class EvilBrain(StubBrain):
            def reason(self, state, task, history):
                return ActionPlan(
                    task_summary="evil",
                    actions=[
                        Action(
                            type="shell",
                            params={"command": "rm -rf /"},
                            reason="evil",
                            expected_change="evil",
                        )
                    ],
                )

        fixture = Path("tests/fixtures/calculator_linux.json")
        perception = MockPerceptionAdapter(fixture)
        action = MockActionAdapter()
        brain = EvilBrain()
        memory = SessionMemory()
        verifier = Verifier()
        safety = SafetyChecker()

        loop = RalphLoop(perception, brain, action, memory, verifier, safety)
        result = loop.run("evil task")
        assert result.status == "aborted"
