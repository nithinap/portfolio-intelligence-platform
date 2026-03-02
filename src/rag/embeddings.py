from __future__ import annotations

import math
import re
from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> dict[str, float]:
        ...


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]{3,}", text.lower())


class SparseEmbeddingProvider:
    """Local deterministic sparse embedding using normalized term frequency."""

    def embed(self, text: str) -> dict[str, float]:
        terms = tokenize(text)
        if not terms:
            return {}
        counts: dict[str, int] = {}
        for term in terms:
            counts[term] = counts.get(term, 0) + 1
        total = float(len(terms))
        return {term: (count / total) for term, count in counts.items()}


def cosine_similarity_sparse(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    for key, val in a.items():
        dot += val * b.get(key, 0.0)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def get_embedding_provider(provider_name: str) -> EmbeddingProvider:
    normalized = provider_name.strip().lower()
    if normalized in {"sparse-local", "local-sparse", "sparse"}:
        return SparseEmbeddingProvider()
    return SparseEmbeddingProvider()
