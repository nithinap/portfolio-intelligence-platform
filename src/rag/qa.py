from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from src.rag.retrieval import retrieve_chunks


@dataclass
class Citation:
    chunk_id: str
    document_id: int
    source: str
    ticker: str | None
    published_at: datetime | None
    excerpt: str
    score: float


@dataclass
class QaResult:
    answer: str
    confidence: float
    citations: list[Citation]


def answer_question(
    session: Session,
    question: str,
    *,
    top_k: int = 5,
    ticker: str | None = None,
    source: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> QaResult:
    retrieved = retrieve_chunks(
        session,
        question,
        top_k=top_k,
        ticker=ticker,
        source=source,
        date_from=date_from,
        date_to=date_to,
    )

    if not retrieved:
        return QaResult(
            answer="No supporting documents matched the request filters and query terms.",
            confidence=0.05,
            citations=[],
        )

    citations: list[Citation] = []
    for item in retrieved:
        citations.append(
            Citation(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                source=item.source,
                ticker=item.ticker,
                published_at=item.published_at,
                excerpt=item.content[:220],
                score=round(item.score, 3),
            )
        )

    summary_lines = [f"- {c.excerpt}" for c in citations[:3]]
    answer = "Grounded summary from retrieved documents:\n" + "\n".join(summary_lines)
    best_score = max(c.score for c in citations)
    confidence = min(0.95, round(0.35 + (0.1 * len(citations)) + (0.35 * best_score), 3))
    return QaResult(answer=answer, confidence=confidence, citations=citations)
