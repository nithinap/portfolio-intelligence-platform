from sqlalchemy import func, select

from src.common.db import SessionLocal
from src.core.models import MarketPriceSnapshot
from src.data_ingestion.pipelines.jobs import run_market_snapshot_job


def test_market_snapshot_job_persists_rows():
    result = run_market_snapshot_job()
    assert result.records_processed >= 1
    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(MarketPriceSnapshot))
        assert total is not None
        assert total >= 1
