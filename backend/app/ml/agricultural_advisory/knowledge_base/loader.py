"""Loads and caches the static knowledge base JSON files.

Loaded once per process (module-level cache) — the advisory engine never
re-reads these files per request, and never makes a network call to fetch
knowledge-base content.

A defensive safety scan runs at load time: if any action text in the
knowledge base matches a chemical-dosage pattern (ml/L, g/L, kg/acre,
concentration, ppm, etc.), loading fails loudly. This is a structural
guarantee that a future edit to the JSON cannot silently introduce a
fabricated pesticide dose — see agricultural_advisory/safety.py.
"""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from pathlib import Path

from app.ml.agricultural_advisory.config import KNOWLEDGE_BASE_DIR

_DOSAGE_PATTERN = re.compile(
    r"\b\d+(\.\d+)?\s*(ml/l|g/l|kg/acre|kg/ha|l/ha|ppm|%\s*(v/v|w/v)|mg/l)\b",
    re.IGNORECASE,
)


class KnowledgeBaseSafetyError(Exception):
    """Raised when the knowledge base contains disallowed content (e.g. a fabricated dosage)."""


@dataclass(frozen=True)
class KnowledgeBase:
    version: str
    pests: dict  # class_name -> pest entry
    diseases: dict  # disease id -> disease entry (currently always empty; see diseases.json)
    crops: dict  # crop id (and aliases) -> crop entry
    sources: dict  # source id -> source entry


def _load_json(filename: str) -> dict:
    path = KNOWLEDGE_BASE_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _scan_for_dosages(entries: list[dict], filename: str) -> None:
    for entry in entries:
        for action in entry.get("actions", []):
            text = action.get("action", "")
            if _DOSAGE_PATTERN.search(text):
                raise KnowledgeBaseSafetyError(
                    f"Rule {action.get('rule_id')} in {filename} appears to contain a "
                    f"fabricated chemical dosage/application rate, which is not allowed: "
                    f"{text!r}"
                )


_lock = threading.Lock()
_cache: KnowledgeBase | None = None


def load_knowledge_base(force_reload: bool = False) -> KnowledgeBase:
    global _cache
    if _cache is not None and not force_reload:
        return _cache

    with _lock:
        if _cache is not None and not force_reload:
            return _cache

        pests_raw = _load_json("pests.json")
        diseases_raw = _load_json("diseases.json")
        crops_raw = _load_json("crops.json")
        sources_raw = _load_json("sources.json")

        _scan_for_dosages(pests_raw.get("pests", []), "pests.json")
        _scan_for_dosages(diseases_raw.get("diseases", []), "diseases.json")

        pests = {entry["class_name"]: entry for entry in pests_raw.get("pests", [])}
        diseases = {entry["id"]: entry for entry in diseases_raw.get("diseases", [])}
        sources = {entry["id"]: entry for entry in sources_raw.get("sources", [])}

        crops = {}
        for entry in crops_raw.get("crops", []):
            crops[entry["id"]] = entry
            for alias in entry.get("aliases", []):
                crops[alias] = entry

        # Referential integrity: every source_id referenced by a rule must exist.
        for entry in pests_raw.get("pests", []):
            for action in entry.get("actions", []):
                for source_id in action.get("source_ids", []):
                    if source_id not in sources:
                        raise KnowledgeBaseSafetyError(
                            f"Rule {action.get('rule_id')} references unknown source_id "
                            f"'{source_id}'."
                        )

        _cache = KnowledgeBase(
            version=pests_raw.get("version", "unknown"),
            pests=pests,
            diseases=diseases,
            crops=crops,
            sources=sources,
        )
        return _cache
