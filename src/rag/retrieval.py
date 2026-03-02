from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.common.settings import get_settings
from src.core.models import DocumentChunk, EmbeddingMetadata
from src.rag.embeddings import cosine_similarity_sparse, get_embedding_provider


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: int
    content: str
    source: str
    ticker: str | None
    published_at: datetime | None
    score: float


def _tokenize(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-zA-Z0-9]{3,}", text.lower())}


def _score(query_terms: set[str], chunk_text: str) -> float:
    if not query_terms:
        return 0.0
    chunk_terms = _tokenize(chunk_text)
    overlap = len(query_terms & chunk_terms)
    return overlap / len(query_terms)


def _load_embedding_lookup(session: Session, chunk_ids: list[str]) -> dict[str, dict[str, float]]:
    if not chunk_ids:
        return {}
    meta_rows = session.scalars(
        select(EmbeddingMetadata).where(EmbeddingMetadata.chunk_id.in_(chunk_ids))
    ).all()
    lookup: dict[str, dict[str, float]] = {}
    for row in meta_rows:
        payload = row.payload or {}
        embedding = payload.get("embedding")
        if isinstance(embedding, dict):
            lookup[row.chunk_id] = {
                str(term): float(value)
                for term, value in embedding.items()
                if isinstance(term, str) and isinstance(value, int | float)
            }
    return lookup


def retrieve_chunks(
    session: Session,
    query: str,
    *,
    top_k: int = 5,
    ticker: str | None = None,
    source: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[RetrievedChunk]:
    settings = get_settings()
    stmt: Select = select(DocumentChunk)
    if ticker:
        stmt = stmt.where(DocumentChunk.ticker == ticker)
    if source:
        stmt = stmt.where(DocumentChunk.source == source)
    if date_from:
        stmt = stmt.where(DocumentChunk.published_at >= date_from)
    if date_to:
        stmt = stmt.where(DocumentChunk.published_at <= date_to)

    # Candidate cap keeps lexical ranking predictable and fast for local development.
    rows = list(session.scalars(stmt.limit(300)))
    query_terms = _tokenize(query)
    lexical_scores = {chunk.chunk_id: _score(query_terms, chunk.content) for chunk in rows}

    ranked: list[tuple[DocumentChunk, float]]
    if settings.retrieval_provider in {"sparse-local", "local-sparse", "sparse"}:
        provider = get_embedding_provider(settings.embedding_provider)
        query_embedding = provider.embed(query)
        embedding_lookup = _load_embedding_lookup(session, [row.chunk_id for row in rows])
        ranked = sorted(
            [
                (
                    chunk,
                    max(
                        cosine_similarity_sparse(
                            query_embedding, embedding_lookup.get(chunk.chunk_id, {})
                        ),
                        lexical_scores.get(chunk.chunk_id, 0.0),
                    ),
                )
                for chunk in rows
            ],
            key=lambda item: item[1],
            reverse=True,
        )
    else:
        ranked = sorted(
            [(chunk, lexical_scores.get(chunk.chunk_id, 0.0)) for chunk in rows],
            key=lambda item: item[1],
            reverse=True,
        )

    results: list[RetrievedChunk] = []
    for chunk, score in ranked[:top_k]:
        if score <= 0:
            continue
        results.append(
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                content=chunk.content,
                source=chunk.source,
                ticker=chunk.ticker,
                published_at=chunk.published_at,
                score=score,
            )
        )
    return results
