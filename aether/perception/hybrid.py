"""Hybrid perception: AT-SPI primary, screenshot+LLM fallback."""

from __future__ import annotations

import time
from typing import Optional, Tuple

import pyatspi

from aether.perception.base import PerceptionAdapter
from aether.perception.screenshot import ScreenshotCapture
from aether.brain.local_llm import LocalLLM
from aether.core.models import UIMap, UIElement, Bounds


class HybridPerceptionAdapter(PerceptionAdapter):
    """Hybrid perception adapter.
    
    PRIMARY path (fast, cheap, accurate):
    1. Query AT-SPI accessibility tree
    2. Find elements by name/role
    
    FALLBACK path (slow, used only when primary fails):
    1. Capture screenshot
    2. Send to local LLM for analysis
    3. LLM suggests coordinates/actions
    
    Philosophy: Never use cloud APIs. Local LLM is fallback only.
    """

    def __init__(self, llm_model: Optional[str] = None):
        self._screenshot = ScreenshotCapture()
        self._llm = LocalLLM(model=llm_model) if llm_model else None
        self._fallback_count = 0
        self._primary_count = 0

    def capture(self) -> UIMap:
        """Capture full UI state via AT-SPI."""
        desktop = pyatspi.Registry.getDesktop(0)
        elements = []
        
        for i in range(desktop.childCount):
            app = desktop.getChildAtIndex(i)
            if app and app.name:
                elements.extend(self._walk_tree(app, app.name))
        
        return UIMap(
            elements=elements,
            screen_width=1920,
            screen_height=1080,
        )

    def _walk_tree(self, node, app_name: str, depth: int = 0) -> list[UIElement]:
        """Recursively walk AT-SPI tree and convert to UIElement."""
        elements = []
        try:
            bounds = None
            try:
                comp = node.queryComponent()
                rect = comp.getExtents(0)
                bounds = Bounds(
                    x=rect.x, y=rect.y,
                    width=rect.width, height=rect.height,
                )
            except Exception:
                pass

            element = UIElement(
                id=f"{app_name}_{node.name or 'unnamed'}_{depth}",
                name=node.name or "",
                role=node.getRoleName(),
                bounds=bounds,
                app=app_name,
                metadata={},
            )
            elements.append(element)

            for i in range(node.childCount):
                elements.extend(self._walk_tree(node.getChildAtIndex(i), app_name, depth + 1))
        except Exception:
            pass
        
        return elements

    def get_active_window(self) -> Optional[UIElement]:
        """Get the currently focused window."""
        desktop = pyatspi.Registry.getDesktop(0)
        for i in range(desktop.childCount):
            app = desktop.getChildAtIndex(i)
            if app and app.name:
                try:
                    state = app.getState()
                    if state.contains(pyatspi.STATE_ACTIVE):
                        return UIElement(
                            id=f"{app.name}_window",
                            name=app.name,
                            role="application",
                            app=app.name,
                        )
                except Exception:
                    pass
        return None

    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen size."""
        try:
            import gi
            gi.require_version('Gdk', '4.0')
            from gi.repository import Gdk
            display = Gdk.Display.get_default()
            monitor = display.get_primary_monitor() or display.get_monitor(0)
            geometry = monitor.get_geometry()
            return (geometry.width, geometry.height)
        except Exception:
            return (1920, 1080)

    def find_element(
        self,
        role: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[UIElement]:
        """Find an element by name/role.
        
        PRIMARY: Search AT-SPI tree.
        FALLBACK: If not found, capture screenshot and ask LLM.
        """
        # PRIMARY: AT-SPI search
        result = self._find_atspi(name, role)
        if result:
            self._primary_count += 1
            return result

        # FALLBACK: Screenshot + LLM
        if self._llm and name:
            self._fallback_count += 1
            return self._find_with_llm(name, role)

        return None

    def _find_atspi(
        self,
        name: Optional[str],
        role: Optional[str],
    ) -> Optional[UIElement]:
        """Search AT-SPI tree for element."""
        desktop = pyatspi.Registry.getDesktop(0)
        
        for i in range(desktop.childCount):
            app = desktop.getChildAtIndex(i)
            if not app or not app.name:
                continue
            
            found = self._search_node(app, name, role, app.name)
            if found:
                return found
        
        return None

    def _search_node(
        self,
        node,
        name: Optional[str],
        role: Optional[str],
        app_name: str,
    ) -> Optional[UIElement]:
        """Recursively search a node."""
        try:
            node_name = node.name or ""
            node_role = node.getRoleName()
            
            match = True
            if name is not None and node_name != name:
                match = False
            if role is not None and node_role != role:
                match = False
            
            if match:
                bounds = None
                try:
                    comp = node.queryComponent()
                    rect = comp.getExtents(0)
                    bounds = Bounds(
                        x=rect.x, y=rect.y,
                        width=rect.width, height=rect.height,
                    )
                except Exception:
                    pass
                
                return UIElement(
                    id=f"{app_name}_{node_name}",
                    name=node_name,
                    role=node_role,
                    bounds=bounds,
                    app=app_name,
                )
            
            for i in range(node.childCount):
                found = self._search_node(node.getChildAtIndex(i), name, role, app_name)
                if found:
                    return found
        except Exception:
            pass
        
        return None

    def _find_with_llm(
        self,
        name: Optional[str],
        role: Optional[str],
    ) -> Optional[UIElement]:
        """FALLBACK: Use screenshot + LLM to find element."""
        if not self._llm or not name:
            return None

        task = f"Find the '{name}'"
        if role:
            task += f" {role}"

        # Capture screenshot
        screenshot_path = self._screenshot.capture()

        # Ask LLM
        result = self._llm.analyze_screenshot(screenshot_path, task)

        if result.get("found"):
            coords = result.get("coordinates", {})
            return UIElement(
                id=f"llm_fallback_{name}",
                name=result.get("element_name", name),
                role=role or "unknown",
                bounds=Bounds(
                    x=coords.get("x", 0),
                    y=coords.get("y", 0),
                    width=50,
                    height=50,
                ),
                app="unknown",
                metadata={
                    "source": "llm_fallback",
                    "confidence": result.get("confidence", 0.5),
                    "reasoning": result.get("reasoning", ""),
                },
            )

        return None

    def get_stats(self) -> dict:
        """Get usage statistics."""
        total = self._primary_count + self._fallback_count
        return {
            "primary_queries": self._primary_count,
            "fallback_queries": self._fallback_count,
            "fallback_rate": self._fallback_count / max(1, total),
        }
