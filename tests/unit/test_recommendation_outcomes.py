from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.common.db import SessionLocal
from src.core.recommendation_outcomes import (
    OutcomeInput,
    classify_outcome,
    record_outcome,
    summarize_outcomes,
)


def test_classify_outcome_rules():
    assert classify_outcome("BUY", 0.01) == "hit"
    assert classify_outcome("BUY", -0.01) == "miss"
    assert classify_outcome("SELL", -0.02) == "hit"
    assert classify_outcome("HOLD", 0.0) == "hit"


def test_record_and_summarize_outcomes():
    ticker = f"T{uuid.uuid4().hex[:5].upper()}"
    with SessionLocal() as session:
        record_outcome(
            session,
            OutcomeInput(
                ticker=ticker,
                horizon="short",
                action="BUY",
                expected_confidence=0.65,
                realized_return=0.01,
                window_days=5,
                realized_at=datetime.now(UTC),
            ),
        )
        record_outcome(
            session,
            OutcomeInput(
                ticker=ticker,
                horizon="short",
                action="BUY",
                expected_confidence=0.7,
                realized_return=-0.02,
                window_days=5,
                realized_at=datetime.now(UTC),
            ),
        )
        summary = summarize_outcomes(session, ticker=ticker, horizon="short")
        assert summary.total >= 2
        assert 0.0 <= summary.hit_rate <= 1.0
        assert -1.0 <= summary.calibration_gap <= 1.0
