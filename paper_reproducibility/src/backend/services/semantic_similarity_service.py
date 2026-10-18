"""SBERT bi-encoder retrieval for semantic test-case deduplication.

The implementation follows the retrieve-and-rerank architecture described by
Reimers & Gurevych (2019): a sentence embedding bi-encoder retrieves the most
semantically similar candidates using cosine similarity; the existing LLM
comparison then acts as the more precise reranker/duplicate decision stage.
"""

from __future__ import annotations

import hashlib
import os
from threading import Lock
from typing import Any, Iterable, List, Sequence, Tuple

import numpy as np
from fastembed import TextEmbedding


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_RETRIEVAL_K = 8

_model = None
_model_lock = Lock()
_embedding_cache: dict[str, np.ndarray] = {}


def _value(case: Any, name: str, default: Any = "") -> Any:
    if isinstance(case, dict):
        return case.get(name, default)
    return getattr(case, name, default)


def semantic_case_text(case: Any) -> str:
    """Build a field-labelled representation of executable test intent."""
    target_symbols = _value(case, "TargetSymbols", []) or []
    if isinstance(target_symbols, str):
        target_symbols = [target_symbols]
    fields = (
        ("title", _value(case, "Title")),
        ("description", _value(case, "Description")),
        ("objective", _value(case, "Objective")),
        ("targets", ", ".join(str(item) for item in target_symbols)),
        ("oracle", _value(case, "OracleType")),
        ("expected", _value(case, "ExpectedResult") or _value(case, "ExpectedBehavior")),
    )
    return "\n".join(f"{label}: {value}" for label, value in fields if value)


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                model_name = os.getenv("TEST_CASE_SEMANTIC_MODEL", DEFAULT_EMBEDDING_MODEL)
                _model = TextEmbedding(model_name=model_name)
    return _model


def _embed_texts(texts: Iterable[str]) -> List[np.ndarray]:
    texts = list(texts)
    keys = [hashlib.sha256(text.encode("utf-8")).hexdigest() for text in texts]
    missing = [(key, text) for key, text in zip(keys, texts) if key not in _embedding_cache]
    if missing:
        vectors = _get_model().embed([text for _, text in missing])
        for (key, _), vector in zip(missing, vectors):
            _embedding_cache[key] = np.asarray(vector, dtype=np.float32)
    return [_embedding_cache[key] for key in keys]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    left_vector = np.asarray(left, dtype=np.float32)
    right_vector = np.asarray(right, dtype=np.float32)
    denominator = float(np.linalg.norm(left_vector) * np.linalg.norm(right_vector))
    return float(np.dot(left_vector, right_vector) / denominator) if denominator else 0.0


def rank_semantic_candidates(
    case: Any,
    candidates: Sequence[Any],
    limit: int | None = None,
) -> List[Tuple[Any, float]]:
    """Return top-k candidates ranked by SBERT cosine similarity."""
    if not candidates:
        return []
    retrieval_k = limit or int(os.getenv("TEST_CASE_SEMANTIC_TOP_K", DEFAULT_RETRIEVAL_K))
    texts = [semantic_case_text(case), *(semantic_case_text(item) for item in candidates)]
    vectors = _embed_texts(texts)
    ranked = [
        (candidate, cosine_similarity(vectors[0], vector), index)
        for index, (candidate, vector) in enumerate(zip(candidates, vectors[1:]))
    ]
    ranked.sort(key=lambda item: (-item[1], item[2]))
    return [(candidate, score) for candidate, score, _ in ranked[:retrieval_k]]
