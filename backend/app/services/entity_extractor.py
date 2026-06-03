from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache

from natasha import Doc, MorphVocab, NewsEmbedding, NewsNERTagger, Segmenter

from app.core.config import get_settings
from app.services.dictionaries import load_dictionary_terms

logger = logging.getLogger(__name__)

GLINER_LABELS = [
    "brand",
    "character",
    "meme",
    "game",
    "film",
    "series",
    "musician",
    "event",
    "spb_place",
    "visual_style",
    "subculture",
]


@dataclass
class ExtractedEntity:
    entity_text: str
    normalized_text: str
    entity_type: str
    source: str
    confidence: float | None


class NatashaExtractor:
    def __init__(self) -> None:
        self.segmenter = Segmenter()
        self.emb = NewsEmbedding()
        self.tagger = NewsNERTagger(self.emb)
        self.morph_vocab = MorphVocab()

    def extract(self, text: str) -> list[ExtractedEntity]:
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_ner(self.tagger)
        results: list[ExtractedEntity] = []
        for span in doc.spans:
            span.normalize(self.morph_vocab)
            entity_type = {
                "PER": "person",
                "ORG": "organization",
                "LOC": "location",
            }.get(span.type)
            if not entity_type:
                continue
            results.append(
                ExtractedEntity(
                    entity_text=span.text,
                    normalized_text=span.normal or span.text,
                    entity_type=entity_type,
                    source="natasha",
                    confidence=None,
                )
            )
        return results


class DictionaryExtractor:
    def __init__(self) -> None:
        self.terms = load_dictionary_terms()

    def extract(self, text: str) -> list[ExtractedEntity]:
        lowered = text.lower()
        results: list[ExtractedEntity] = []
        for item in self.terms:
            if re.search(rf"(?<!\w){re.escape(item.term.lower())}(?!\w)", lowered):
                results.append(
                    ExtractedEntity(
                        entity_text=item.term,
                        normalized_text=item.normalized,
                        entity_type=item.type,
                        source="dictionary",
                        confidence=1.0,
                    )
                )
        return results


class GLiNERExtractor:
    def __init__(self) -> None:
        self._model = None
        self._load_error: str | None = None

    def _get_model(self):
        if self._model is not None:
            return self._model
        if self._load_error is not None:
            raise RuntimeError(self._load_error)
        try:
            from gliner import GLiNER

            self._model = GLiNER.from_pretrained(get_settings().gliner_model)
            return self._model
        except Exception as exc:  # pragma: no cover - runtime dependent
            self._load_error = str(exc)
            logger.warning("GLiNER unavailable: %s", exc)
            raise RuntimeError(self._load_error) from exc

    def extract(self, text: str) -> list[ExtractedEntity]:
        try:
            model = self._get_model()
        except RuntimeError:
            return []
        try:
            predictions = model.predict_entities(text, GLINER_LABELS)
        except Exception as exc:  # pragma: no cover - runtime dependent
            logger.warning("GLiNER prediction failed: %s", exc)
            return []
        results: list[ExtractedEntity] = []
        for item in predictions:
            label = item.get("label", "unknown")
            results.append(
                ExtractedEntity(
                    entity_text=item.get("text", ""),
                    normalized_text=item.get("text", "").strip(),
                    entity_type=label,
                    source="gliner",
                    confidence=float(item.get("score")) if item.get("score") is not None else None,
                )
            )
        return results


class EntityExtractor:
    def __init__(self) -> None:
        self.natasha = NatashaExtractor()
        self.gliner = GLiNERExtractor()
        self.dictionary = DictionaryExtractor()

    def extract(self, text: str) -> list[ExtractedEntity]:
        candidates = self.natasha.extract(text) + self.gliner.extract(text) + self.dictionary.extract(text)
        unique: dict[tuple[str, str, str], ExtractedEntity] = {}
        for item in candidates:
            key = (item.normalized_text.lower(), item.entity_type, item.source)
            previous = unique.get(key)
            if previous is None or (item.confidence or 0.0) > (previous.confidence or 0.0):
                unique[key] = item
        return list(unique.values())


@lru_cache
def get_entity_extractor() -> EntityExtractor:
    return EntityExtractor()

