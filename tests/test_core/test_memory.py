from datetime import datetime

from aether.core.memory import SessionMemory
from aether.core.models import Action, ActionRecord


class TestSessionMemory:
    def test_history_appends(self):
        mem = SessionMemory()
        record = ActionRecord(
            action=Action(
                type="click",
                params={"x": 1, "y": 2},
                reason="test",
                expected_change="test",
            )
        )
        mem.history.append(record)
        assert len(mem.history) == 1

    def test_history_max_length(self):
        mem = SessionMemory(max_history=3)
        for i in range(5):
            record = ActionRecord(
                action=Action(
                    type="click",
                    params={"x": i, "y": i},
                    reason="test",
                    expected_change="test",
                )
            )
            mem.history.append(record)
        assert len(mem.history) == 3
        assert mem.history[0].action.params["x"] == 2

    def test_failed_attempts_tracking(self):
        mem = SessionMemory()
        mem.failed_attempts["click"] = 2
        assert mem.failed_attempts["click"] == 2

    def test_update_progress(self):
        mem = SessionMemory()
        mem.update_progress("test task", done=True)
        assert mem.progress.current_task == "test task"
        assert mem.progress.done is True
