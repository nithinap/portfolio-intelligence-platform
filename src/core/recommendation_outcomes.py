from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.core.models import RecommendationOutcome


@dataclass
class OutcomeInput:
    ticker: str
    horizon: str
    action: str
    expected_confidence: float
    realized_return: float
    window_days: int
    realized_at: datetime
    recommendation_id: int | None = None
    details: dict | None = None


@dataclass
class OutcomeRecordResult:
    id: int
    outcome_label: str


@dataclass
class OutcomeSummary:
    total: int
    hit_rate: float
    neutral_rate: float
    avg_realized_return: float
    avg_expected_confidence: float
    calibration_gap: float
    recent_hit_rate_drift: float


def classify_outcome(action: str, realized_return: float) -> str:
    normalized = action.strip().upper()
    if normalized == "BUY":
        if realized_return > 0:
            return "hit"
        if realized_return < 0:
            return "miss"
        return "neutral"
    if normalized == "SELL":
        if realized_return < 0:
            return "hit"
        if realized_return > 0:
            return "miss"
        return "neutral"
    if abs(realized_return) <= 0.002:
        return "hit"
    return "miss"


def record_outcome(session: Session, payload: OutcomeInput) -> OutcomeRecordResult:
    label = classify_outcome(payload.action, payload.realized_return)
    row = RecommendationOutcome(
        recommendation_id=payload.recommendation_id,
        ticker=payload.ticker.upper(),
        horizon=payload.horizon,
        action=payload.action.upper(),
        expected_confidence=payload.expected_confidence,
        realized_return=payload.realized_return,
        window_days=payload.window_days,
        outcome_label=label,
        details=payload.details or {},
        realized_at=payload.realized_at,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return OutcomeRecordResult(id=row.id, outcome_label=label)


def summarize_outcomes(
    session: Session,
    *,
    ticker: str | None = None,
    horizon: str | None = None,
    lookback_days: int | None = None,
) -> OutcomeSummary:
    stmt: Select = select(RecommendationOutcome)
    if ticker:
        stmt = stmt.where(RecommendationOutcome.ticker == ticker.upper())
    if horizon:
        stmt = stmt.where(RecommendationOutcome.horizon == horizon)
    if lookback_days:
        since = datetime.now(UTC) - timedelta(days=max(1, lookback_days))
        stmt = stmt.where(RecommendationOutcome.realized_at >= since)

    rows = session.scalars(stmt.order_by(RecommendationOutcome.realized_at.asc()).limit(5000)).all()
    if not rows:
        return OutcomeSummary(
            total=0,
            hit_rate=0.0,
            neutral_rate=0.0,
            avg_realized_return=0.0,
            avg_expected_confidence=0.0,
            calibration_gap=0.0,
            recent_hit_rate_drift=0.0,
        )

    total = len(rows)
    hit_count = sum(1 for row in rows if row.outcome_label == "hit")
    neutral_count = sum(1 for row in rows if row.outcome_label == "neutral")
    avg_realized = sum(row.realized_return for row in rows) / total
    avg_conf = sum(row.expected_confidence for row in rows) / total
    hit_rate = hit_count / total
    neutral_rate = neutral_count / total
    calibration_gap = avg_conf - hit_rate

    midpoint = total // 2
    older = rows[:midpoint] if midpoint else rows
    recent = rows[midpoint:] if midpoint else rows
    older_hit = (
        sum(1 for row in older if row.outcome_label == "hit") / len(older) if older else 0.0
    )
    recent_hit = (
        sum(1 for row in recent if row.outcome_label == "hit") / len(recent) if recent else 0.0
    )
    drift = recent_hit - older_hit

    return OutcomeSummary(
        total=total,
        hit_rate=round(hit_rate, 3),
        neutral_rate=round(neutral_rate, 3),
        avg_realized_return=round(avg_realized, 6),
        avg_expected_confidence=round(avg_conf, 3),
        calibration_gap=round(calibration_gap, 3),
        recent_hit_rate_drift=round(drift, 3),
    )
