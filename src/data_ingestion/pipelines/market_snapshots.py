from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.core.models import MarketPriceSnapshot
from src.data_ingestion.connectors import PriceBar


@dataclass
class SnapshotWriteResult:
    rows_written: int


def write_market_snapshots(session: Session, bars: list[PriceBar]) -> SnapshotWriteResult:
    if not bars:
        return SnapshotWriteResult(rows_written=0)

    for bar in bars:
        session.add(
            MarketPriceSnapshot(
                ticker=bar.ticker,
                interval=bar.interval,
                ts_utc=bar.ts_utc,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                source=bar.source,
            )
        )
    session.commit()
    return SnapshotWriteResult(rows_written=len(bars))
