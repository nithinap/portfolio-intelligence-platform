from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.core.models import Document, Signal

POSITIVE_WORDS = {
    "strong",
    "improved",
    "growth",
    "accelerated",
    "record",
    "gain",
    "beat",
    "positive",
    "upside",
    "expansion",
}

NEGATIVE_WORDS = {
    "weak",
    "decline",
    "slowed",
    "drop",
    "miss",
    "negative",
    "downside",
    "risk",
    "contraction",
    "loss",
}


@dataclass
class SentimentAggregationResult:
    rows_written: int
    tickers_processed: int


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]{3,}", text.lower())


def _score_text(text: str) -> float:
    terms = _tokenize(text)
    if not terms:
        return 0.0
    pos = sum(1 for term in terms if term in POSITIVE_WORDS)
    neg = sum(1 for term in terms if term in NEGATIVE_WORDS)
    return (pos - neg) / len(terms)


def compute_daily_sentiment_signals(
    session: Session,
    *,
    ticker: str | None = None,
    source: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> SentimentAggregationResult:
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
        return SentimentAggregationResult(rows_written=0, tickers_processed=0)

    grouped: dict[str, list[float]] = {}
    for doc in docs:
        if not doc.ticker:
            continue
        grouped.setdefault(doc.ticker, []).append(_score_text(doc.content))

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
                },
            )
        )
        rows_written += 1

    session.commit()
    return SentimentAggregationResult(rows_written=rows_written, tickers_processed=len(grouped))
