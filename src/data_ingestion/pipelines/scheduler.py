from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.common.bootstrap import bootstrap_database
from src.common.db import SessionLocal
from src.common.logging import configure_logging, get_logger, set_correlation_id
from src.common.observability import JOB_COUNTER, JOB_DURATION
from src.common.settings import get_settings
from src.core.models import JobAudit
from src.data_ingestion.pipelines.jobs import (
    JobResult,
    run_filings_fetch_job,
    run_market_snapshot_job,
    run_news_fetch_job,
)

logger = get_logger("jobs")
settings = get_settings()
configure_logging(settings.log_level)


def _run_with_audit(session: Session, job_name: str, fn: Callable[[], JobResult]) -> None:
    correlation_id = set_correlation_id()
    start = datetime.now(UTC)
    t0 = time.perf_counter()
    status = "success"
    details: dict = {}
    records_processed = 0

    try:
        result = fn()
        details = result.details
        records_processed = result.records_processed
    except Exception as exc:
        status = "failed"
        details = {"error": str(exc)}
        logger.exception("job_failed", job=job_name, correlation_id=correlation_id)

    duration = time.perf_counter() - t0
    finished = datetime.now(UTC)
    JOB_COUNTER.labels(job_name, status).inc()
    JOB_DURATION.labels(job_name).observe(duration)

    session.add(
        JobAudit(
            job_name=job_name,
            status=status,
            started_at=start,
            finished_at=finished,
            duration_ms=int(duration * 1000),
            records_processed=records_processed,
            details=details,
            correlation_id=correlation_id,
        )
    )
    session.commit()
    logger.info(
        "job_completed",
        job=job_name,
        status=status,
        duration_ms=int(duration * 1000),
        records_processed=records_processed,
        correlation_id=correlation_id,
    )


def run_all_jobs() -> None:
    bootstrap_database()
    with SessionLocal() as session:
        _run_with_audit(session, "market_snapshot", run_market_snapshot_job)
        _run_with_audit(session, "news_fetch", run_news_fetch_job)
        _run_with_audit(session, "filings_fetch", run_filings_fetch_job)


if __name__ == "__main__":
    run_all_jobs()
