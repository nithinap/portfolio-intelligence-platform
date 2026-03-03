from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from src.common.settings import get_settings
from src.rag.answer_generation import (
    DeterministicAnswerGenerator,
    SourceContext,
    get_answer_generator,
)
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
    answer_provider: str
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
    settings = get_settings()
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
            answer_provider="none",
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

    contexts = [
        SourceContext(
            chunk_id=c.chunk_id,
            source=c.source,
            ticker=c.ticker,
            published_at=c.published_at,
            excerpt=c.excerpt,
        )
        for c in citations
    ]
    configured_provider = settings.qa_answer_provider.strip().lower()
    generator = get_answer_generator(
        configured_provider,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.qa_openai_model,
        openai_base_url=settings.qa_openai_base_url,
        openai_timeout_seconds=settings.qa_openai_timeout_seconds,
    )
    answer = generator.generate(question, contexts)
    answer_provider = configured_provider
    if not answer:
        fallback = DeterministicAnswerGenerator()
        answer = fallback.generate(question, contexts) or (
            "No grounded evidence was available to answer this question."
        )
        answer_provider = "deterministic-fallback"

    best_score = max(c.score for c in citations)
    confidence = min(0.95, round(0.35 + (0.1 * len(citations)) + (0.35 * best_score), 3))
    return QaResult(
        answer=answer,
        confidence=confidence,
        answer_provider=answer_provider,
        citations=citations,
    )
