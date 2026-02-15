from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class JobResult:
    records_processed: int
    details: dict


def run_market_snapshot_job() -> JobResult:
    now = datetime.now(UTC).isoformat()
    return JobResult(records_processed=12, details={"source": "stub", "timestamp": now})


def run_news_fetch_job() -> JobResult:
    now = datetime.now(UTC).isoformat()
    return JobResult(records_processed=8, details={"source": "stub", "timestamp": now})


def run_filings_fetch_job() -> JobResult:
    now = datetime.now(UTC).isoformat()
    return JobResult(records_processed=3, details={"source": "stub", "timestamp": now})
