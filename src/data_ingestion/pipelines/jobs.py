from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from src.common.db import SessionLocal
from src.common.settings import get_settings
from src.data_ingestion.connectors import get_market_data_provider
from src.data_ingestion.pipelines.market_snapshots import write_market_snapshots

settings = get_settings()


@dataclass
class JobResult:
    records_processed: int
    details: dict


def run_market_snapshot_job() -> JobResult:
    tickers = [t.strip().upper() for t in settings.market_data_tickers.split(",") if t.strip()]
    provider = get_market_data_provider(settings.market_data_provider)
    bars = provider.fetch_daily_bars(
        tickers=tickers, lookback_days=settings.market_data_lookback_days
    )
    with SessionLocal() as session:
        written = write_market_snapshots(session, bars)
    now = datetime.now(UTC).isoformat()
    source = bars[0].source if bars else settings.market_data_provider
    return JobResult(
        records_processed=written.rows_written,
        details={
            "source": source,
            "timestamp": now,
            "tickers": tickers,
            "lookback_days": settings.market_data_lookback_days,
        },
    )


def run_news_fetch_job() -> JobResult:
    now = datetime.now(UTC).isoformat()
    return JobResult(records_processed=8, details={"source": "stub", "timestamp": now})


def run_filings_fetch_job() -> JobResult:
    now = datetime.now(UTC).isoformat()
    return JobResult(records_processed=3, details={"source": "stub", "timestamp": now})
