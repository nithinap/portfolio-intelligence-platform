from sqlalchemy import func, select

from src.common.db import SessionLocal
from src.core.models import JobAudit
from src.data_ingestion.pipelines.scheduler import run_all_jobs


def test_scheduler_writes_audit_rows():
    run_all_jobs()
    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(JobAudit))
        assert total is not None
        assert total >= 3
