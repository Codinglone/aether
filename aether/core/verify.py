from __future__ import annotations

from aether.core.models import UIMap, Action, VerificationResult


class Verifier:
    def verify(self, before: UIMap, after: UIMap, action: Action) -> VerificationResult:
        # Strategy 1: Tree diff (element name/state changes)
        tree_result = self._check_tree_diff(before, after)
        if tree_result.success:
            return tree_result

        # Strategy 2: Focus tracking
        focus_result = self._check_focus_change(before, after)
        if focus_result.success:
            return focus_result

        # Strategy 3: Window tracking
        window_result = self._check_window_change(before, after)
        if window_result.success:
            return window_result

        # No strategy matched
        return VerificationResult(
            success=False,
            confidence=0.0,
            matched_strategy="none",
            details="No state change detected",
        )

    def _check_tree_diff(self, before: UIMap, after: UIMap) -> VerificationResult:
        before_map = self._flatten_elements(before.elements)
        after_map = self._flatten_elements(after.elements)

        changed = []
        for eid, after_elem in after_map.items():
            if eid in before_map:
                before_elem = before_map[eid]
                if before_elem.name != after_elem.name or before_elem.state != after_elem.state:
                    changed.append(eid)

        if changed:
            return VerificationResult(
                success=True,
                confidence=min(1.0, 0.5 + 0.1 * len(changed)),
                matched_strategy="tree_diff",
                details=f"Elements changed: {changed}",
            )
        return VerificationResult(success=False, confidence=0.0, matched_strategy="tree_diff")

    def _flatten_elements(self, elements):
        result = {}
        for elem in elements:
            result[elem.id] = elem
            result.update(self._flatten_elements(elem.children))
        return result

    def _check_focus_change(self, before: UIMap, after: UIMap) -> VerificationResult:
        if before.focused_element != after.focused_element:
            return VerificationResult(
                success=True,
                confidence=0.8,
                matched_strategy="focus",
                details="Focused element changed",
            )
        return VerificationResult(success=False, confidence=0.0, matched_strategy="focus")

    def _check_window_change(self, before: UIMap, after: UIMap) -> VerificationResult:
        if before.active_window != after.active_window:
            return VerificationResult(
                success=True,
                confidence=0.9,
                matched_strategy="window",
                details="Active window changed",
            )
        return VerificationResult(success=False, confidence=0.0, matched_strategy="window")


class DummyVerifier(Verifier):
    """Always-succeed verifier for demos."""

    def verify(self, before, after, action):
        return VerificationResult(
            success=True, confidence=1.0, matched_strategy="dummy"
        )
