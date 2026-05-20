from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class KnowledgeStore:
    """Stores learned UI quirks in both human-readable markdown and machine-readable JSON."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir).expanduser() if data_dir else Path.home() / ".local" / "share" / "aether"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._md_file = self.data_dir / "knowledge.md"
        self._json_file = self.data_dir / "knowledge.json"
        self._entries: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Load existing knowledge entries from JSON."""
        if self._json_file.exists():
            try:
                with open(self._json_file) as f:
                    data = json.load(f)
                self._entries = data.get("entries", [])
            except (json.JSONDecodeError, TypeError):
                self._entries = []
        else:
            self._entries = []

    def _save(self) -> None:
        """Save entries to both JSON and Markdown."""
        # JSON
        data = {"entries": self._entries}
        tmp_json = self._json_file.with_suffix(".tmp")
        with open(tmp_json, "w") as f:
            json.dump(data, f, indent=2)
        tmp_json.replace(self._json_file)

        # Markdown
        md_lines = ["# Aether Knowledge Base\n", "Learned UI behaviors and workarounds.\n"]
        for entry in self._entries:
            md_lines.append(f"\n## {entry['app']}\n")
            md_lines.append(f"- **Pattern:** {entry['pattern']}\n")
            md_lines.append(f"- **Learned:** {entry['action']}\n")
            md_lines.append(f"- **Confidence:** {entry['confidence']}\n")
            md_lines.append(f"- **Date:** {entry['date']}\n")

        tmp_md = self._md_file.with_suffix(".tmp")
        with open(tmp_md, "w") as f:
            f.writelines(md_lines)
        tmp_md.replace(self._md_file)

    def add_entry(
        self,
        app: str,
        pattern: str,
        action: str,
        confidence: float = 0.5,
    ) -> None:
        """Add a new knowledge entry."""
        self._entries.append(
            {
                "app": app,
                "pattern": pattern,
                "action": action,
                "confidence": confidence,
                "date": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save()

    def search_for_app(self, app: str, pattern_hint: Optional[str] = None) -> list[dict]:
        """Find knowledge entries for a given app, optionally filtered by pattern substring."""
        results = [e for e in self._entries if e["app"].lower() == app.lower()]
        if pattern_hint:
            hint_lower = pattern_hint.lower()
            results = [e for e in results if hint_lower in e["pattern"].lower() or e["pattern"].lower() in hint_lower]
        return results

    def render_for_prompt(self, app: str, task: str) -> str:
        """Render relevant knowledge as markdown text for LLM prompt injection."""
        results = self.search_for_app(app, pattern_hint=task)
        if not results:
            return ""

        lines = ["### Learned Tips"]
        for entry in results:
            lines.append(f"- {entry['pattern']}: {entry['action']} (confidence: {entry['confidence']})")
        return "\n".join(lines)
