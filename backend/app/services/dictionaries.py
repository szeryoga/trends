from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class DictionaryTerm:
    term: str
    normalized: str
    type: str


@lru_cache
def load_dictionary_terms() -> list[DictionaryTerm]:
    root = Path(__file__).resolve().parents[3] / "dictionaries"
    items: list[DictionaryTerm] = []
    for path in sorted(root.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        for entry in raw:
            items.append(
                DictionaryTerm(
                    term=entry["term"],
                    normalized=entry["normalized"],
                    type=entry["type"],
                )
            )
    return items

