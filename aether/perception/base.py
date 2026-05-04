from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from aether.core.models import UIMap, UIElement


class PerceptionAdapter(ABC):
    @abstractmethod
    def capture(self) -> UIMap:
        ...

    @abstractmethod
    def get_active_window(self) -> Optional[UIElement]:
        ...

    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        ...

    @abstractmethod
    def find_element(self, role: Optional[str] = None, name: Optional[str] = None) -> Optional[UIElement]:
        ...
