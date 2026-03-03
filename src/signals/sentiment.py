from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.common.settings import get_settings
from src.core.models import Document, Signal
from src.signals.sentiment_scoring import score_with_fallback


@dataclass
class SentimentAggregationResult:
    rows_written: int
    tickers_processed: int
    provider_counts: dict[str, int]


def compute_daily_sentiment_signals(
    session: Session,
    *,
    ticker: str | None = None,
    source: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> SentimentAggregationResult:
    settings = get_settings()
    stmt: Select = select(Document).where(Document.ticker.is_not(None))
    if ticker:
        stmt = stmt.where(Document.ticker == ticker.upper())
    if source:
        stmt = stmt.where(Document.source == source)
    if date_from:
        stmt = stmt.where(Document.published_at >= date_from)
    if date_to:
        stmt = stmt.where(Document.published_at <= date_to)

    docs = session.scalars(stmt.limit(1000)).all()
    if not docs:
        return SentimentAggregationResult(
            rows_written=0, tickers_processed=0, provider_counts={}
        )

    grouped: dict[str, list[float]] = {}
    provider_counts: dict[str, int] = {}
    for doc in docs:
        if not doc.ticker:
            continue
        scored = score_with_fallback(
            doc.content,
            primary_provider=settings.sentiment_provider,
            openai_api_key=settings.openai_api_key,
            openai_model=settings.sentiment_openai_model,
            openai_base_url=settings.sentiment_openai_base_url,
            openai_timeout_seconds=settings.sentiment_openai_timeout_seconds,
        )
        grouped.setdefault(doc.ticker, []).append(scored.value)
        provider_counts[scored.provider_used] = provider_counts.get(scored.provider_used, 0) + 1

    rows_written = 0
    as_of = datetime.now(UTC)
    for ticker_key, scores in grouped.items():
        if not scores:
            continue
        avg = sum(scores) / len(scores)
        dispersion = (max(scores) - min(scores)) if len(scores) > 1 else 0.0
        session.add(
            Signal(
                ticker=ticker_key,
                signal_type="sentiment_daily",
                value=round(avg, 6),
                confidence=min(1.0, round(0.4 + (0.1 * min(len(scores), 6)), 3)),
                as_of=as_of,
                details={
                    "doc_count": len(scores),
                    "score_min": round(min(scores), 6),
                    "score_max": round(max(scores), 6),
                    "dispersion": round(dispersion, 6),
                    "source_filter": source,
                    "sentiment_provider": settings.sentiment_provider,
                },
            )
        )
        rows_written += 1

    session.commit()
    return SentimentAggregationResult(
        rows_written=rows_written,
        tickers_processed=len(grouped),
        provider_counts=provider_counts,
    )
