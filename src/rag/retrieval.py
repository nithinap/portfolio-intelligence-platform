from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.core.models import DocumentChunk


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
    ranked = sorted(
        rows,
        key=lambda chunk: _score(query_terms, chunk.content),
        reverse=True,
    )

    results: list[RetrievedChunk] = []
    for chunk in ranked[:top_k]:
        score = _score(query_terms, chunk.content)
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
