"""Minimal offline history store for temporal (trend) reasoning.

Deliberately not a database — a single append-only JSONL file, consistent
with this project's "no unnecessary microservices / offline-capable"
constraint. Each line is one past observation of one pest species at one
farm/field. The advisory engine appends to this after every analysis and
reads from it (merged with any client-supplied historical_observations) to
compute trends.

This is a prototype persistence mechanism. For multi-instance or
concurrent-writer deployments, replace with a real datastore — the
`HistoryStore` interface (append/query) is designed to be swapped without
touching callers.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from app.ml.agricultural_advisory.config import settings

_lock = threading.Lock()


class HistoryStore:
    def __init__(self, path: Path | None = None):
        self.path = path or settings.history_path

    def append(self, record: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

    def query(
        self, farm_id: str | None, field_id: str | None, pest_name: str, limit: int | None = None
    ) -> list[dict]:
        if not self.path.exists():
            return []
        limit = limit or settings.history_lookback
        matches = []
        with _lock:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if (
                        record.get("pest_name") == pest_name
                        and record.get("farm_id") == farm_id
                        and record.get("field_id") == field_id
                    ):
                        matches.append(record)
        matches.sort(key=lambda r: r.get("timestamp", ""))
        return matches[-limit:]


_default_store: HistoryStore | None = None


def get_history_store() -> HistoryStore:
    global _default_store
    if _default_store is None:
        _default_store = HistoryStore()
    return _default_store
