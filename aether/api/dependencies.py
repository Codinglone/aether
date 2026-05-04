from __future__ import annotations

from typing import Optional

from aether.core.loop import RalphLoop


# Global singleton for Phase 0 stub
_loop: Optional[RalphLoop] = None


def get_loop() -> Optional[RalphLoop]:
    return _loop


def set_loop(loop: RalphLoop) -> None:
    global _loop
    _loop = loop
