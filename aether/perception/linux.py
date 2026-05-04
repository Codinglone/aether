from __future__ import annotations

from typing import Optional, Tuple

from aether.core.models import UIMap, UIElement, Bounds
from aether.perception.base import PerceptionAdapter


def _get_screen_size() -> Tuple[int, int]:
    """Get the primary screen size using Gdk or fallback."""
    try:
        import gi
        gi.require_version('Gdk', '4.0')
        from gi.repository import Gdk
        display = Gdk.Display.get_default()
        if display:
            monitor = display.get_primary_monitor() or display.get_monitor(0)
            if monitor:
                geometry = monitor.get_geometry()
                return (geometry.width, geometry.height)
    except Exception:
        pass
    return (1920, 1080)


def _atspi_rect_to_bounds(rect) -> Bounds:
    return Bounds(x=rect.x, y=rect.y, width=rect.width, height=rect.height)


def _atspi_state_to_set(state_set) -> set[str]:
    states = set()
    try:
        for state in state_set.get_states():
            try:
                states.add(state.value_nick)
            except Exception:
                pass
    except Exception:
        pass
    return states


def _walk_atspi_tree(node, parent_id: Optional[str] = None, max_depth: int = 15, current_depth: int = 0) -> Optional[UIElement]:
    """Recursively convert an AT-SPI node to a UIElement."""
    try:
        role = node.get_role_name()
        name = node.name or ""
        description = node.description or ""
        
        bounds = Bounds(x=0, y=0, width=0, height=0)
        try:
            comp = node.query_component()
            if comp:
                rect = comp.get_extents(0)
                bounds = _atspi_rect_to_bounds(rect)
        except Exception:
            pass
        
        state = _atspi_state_to_set(node.get_state_set())
        elem_id = f"{role}-{name}-{bounds.x}-{bounds.y}"
        
        children = []
        if current_depth < max_depth:
            try:
                for i in range(min(node.childCount, 50)):  # Limit children per node
                    child = node.getChildAtIndex(i)
                    if child:
                        child_elem = _walk_atspi_tree(child, parent_id=elem_id, max_depth=max_depth, current_depth=current_depth + 1)
                        if child_elem:
                            children.append(child_elem)
            except Exception:
                pass
        
        return UIElement(
            id=elem_id,
            role=role,
            name=name,
            description=description or None,
            bounds=bounds,
            state=state,
            children=children,
            parent_id=parent_id,
        )
    except Exception:
        return None


class LinuxPerceptionAdapter(PerceptionAdapter):
    """Linux perception using AT-SPI2 via pyatspi."""

    def capture(self) -> UIMap:
        try:
            import pyatspi
            desktop = pyatspi.Registry.getDesktop(0)
            elements = []
            
            for i in range(desktop.childCount):
                app = desktop.getChildAtIndex(i)
                if app is None:
                    continue
                try:
                    for j in range(app.childCount):
                        window = app.getChildAtIndex(j)
                        if window is None:
                            continue
                        elem = _walk_atspi_tree(window)
                        if elem:
                            elements.append(elem)
                except Exception:
                    continue
            
            # Find focused element
            focused_element = None
            try:
                focused = pyatspi.Registry.getFocusObject()
                if focused:
                    focused_element = _walk_atspi_tree(focused)
            except Exception:
                pass
            
            # Find active window
            active_window = None
            for elem in elements:
                if "active" in elem.state:
                    active_window = elem
                    break
            
            return UIMap(
                screen_size=_get_screen_size(),
                elements=elements,
                active_window=active_window,
                focused_element=focused_element,
            )
        except Exception as e:
            return UIMap(screen_size=_get_screen_size(), elements=[])

    def get_active_window(self) -> Optional[UIElement]:
        uimap = self.capture()
        return uimap.active_window

    def get_screen_size(self) -> Tuple[int, int]:
        return _get_screen_size()

    def find_element(self, role: Optional[str] = None, name: Optional[str] = None) -> Optional[UIElement]:
        uimap = self.capture()
        
        def _search(elements):
            for elem in elements:
                match = True
                if role is not None and elem.role != role:
                    match = False
                if name is not None and elem.name != name:
                    match = False
                if match:
                    return elem
                found = _search(elem.children)
                if found:
                    return found
            return None
        
        return _search(uimap.elements)
