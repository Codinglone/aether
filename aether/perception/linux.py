from __future__ import annotations

from typing import Optional, Tuple

from aether.core.models import UIMap, UIElement
from aether.perception.base import PerceptionAdapter


class LinuxPerceptionAdapter(PerceptionAdapter):
    """Linux perception using AT-SPI2 via pyatspi2.
    This is a stub for Phase 0. Full implementation requires pyatspi2.
    """

    def capture(self) -> UIMap:
        return UIMap(screen_size=(1920, 1080), elements=[])

    def get_active_window(self) -> Optional[UIElement]:
        return None

    def get_screen_size(self) -> Tuple[int, int]:
        return (1920, 1080)

    def find_element(self, role: Optional[str] = None, name: Optional[str] = None) -> Optional[UIElement]:
        return None
