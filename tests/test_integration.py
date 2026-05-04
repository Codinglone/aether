from pathlib import Path

from aether.core.loop import RalphLoop
from aether.core.brain import StubBrain
from aether.core.safety import SafetyChecker
from aether.core.verify import Verifier
from aether.core.memory import SessionMemory
from tests.harness import MockPerceptionAdapter, MockActionAdapter


class TestIntegration:
    def test_calculator_click(self):
        fixture = Path("tests/fixtures/calculator_linux.json")
        perception = MockPerceptionAdapter(fixture)
        action = MockActionAdapter()
        brain = StubBrain()
        memory = SessionMemory()
        verifier = Verifier()
        safety = SafetyChecker()

        loop = RalphLoop(perception, brain, action, memory, verifier, safety)
        result = loop.run("Click the 2 button")

        assert result.status == "success"
        assert result.actions_taken >= 1
        assert any(a["type"] == "click" for a in action.executed_actions)
