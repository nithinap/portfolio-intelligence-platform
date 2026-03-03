from __future__ import annotations

import subprocess
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select, text
from sqlalchemy.orm import Session

from src.common.bootstrap import bootstrap_database
from src.common.db import get_db_session
from src.common.errors import ErrorResponse
from src.common.logging import configure_logging, get_correlation_id, get_logger, set_correlation_id
from src.common.observability import MetricsMiddleware, metrics_response, setup_tracing
from src.common.settings import get_settings
from src.core.models import MarketPriceSnapshot
from src.data_ingestion.pipelines.document_ingestion import ingest_documents
from src.data_ingestion.pipelines.jobs import run_market_snapshot_job
from src.data_ingestion.schemas import IngestDocumentInput
from src.rag.chunking_benchmark import ChunkingBenchmarkCase, benchmark_chunkers
from src.rag.evaluation import QaEvalCase, evaluate_qa_cases
from src.rag.qa import answer_question
from src.signals import compute_daily_sentiment_signals

settings = get_settings()
configure_logging(settings.log_level)
setup_tracing(settings.app_name)
logger = get_logger("api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_database()
    logger.info("app_start", app_name=settings.app_name, env=settings.app_env)
    yield
    logger.info("app_stop", app_name=settings.app_name, env=settings.app_env)


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(MetricsMiddleware)


class IngestRequest(BaseModel):
    documents: list[IngestDocumentInput] = Field(min_length=1)


class IngestResponse(BaseModel):
    documents_ingested: int
    chunks_ingested: int


class QaRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)
    ticker: str | None = None
    source: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class QaCitation(BaseModel):
    chunk_id: str
    document_id: int
    source: str
    ticker: str | None
    published_at: datetime | None
    excerpt: str
    score: float


class QaResponse(BaseModel):
    answer: str
    confidence: float
    answer_provider: str
    citations: list[QaCitation]


class QaEvalCaseRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)
    ticker: str | None = None
    source: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    min_citations: int = Field(default=1, ge=0, le=20)
    min_confidence: float = Field(default=0.2, ge=0.0, le=1.0)


class QaEvalRequest(BaseModel):
    cases: list[QaEvalCaseRequest] = Field(min_length=1)


class QaEvalCaseResponse(BaseModel):
    question: str
    confidence: float
    citation_count: int
    passed: bool
    reasons: list[str]


class QaEvalResponse(BaseModel):
    total_cases: int
    pass_rate: float
    citation_coverage: float
    avg_confidence: float
    cases: list[QaEvalCaseResponse]


class MarketIngestResponse(BaseModel):
    records_processed: int
    details: dict


class MarketSnapshotResponse(BaseModel):
    ticker: str
    interval: str
    ts_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str


class SentimentComputeRequest(BaseModel):
    ticker: str | None = None
    source: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class SentimentComputeResponse(BaseModel):
    rows_written: int
    tickers_processed: int
    provider_counts: dict[str, int]


class ChunkingBenchmarkCaseRequest(BaseModel):
    question: str = Field(min_length=3)
    content: str = Field(min_length=10)


class ChunkingBenchmarkRequest(BaseModel):
    cases: list[ChunkingBenchmarkCaseRequest] = Field(min_length=1)
    threshold: float = Field(default=0.35, ge=0.0, le=1.0)


class ChunkingBenchmarkMetricsResponse(BaseModel):
    provider: str
    avg_best_overlap: float
    pass_rate: float
    avg_chunks_per_case: float
    avg_chunk_chars: float
    runtime_ms: float


class ChunkingBenchmarkResponse(BaseModel):
    threshold: float
    winner: str
    metrics: list[ChunkingBenchmarkMetricsResponse]


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    incoming = request.headers.get("x-correlation-id")
    cid = set_correlation_id(incoming)
    response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    cid = get_correlation_id()
    logger.exception("unhandled_exception", correlation_id=cid, error=str(exc))
    payload = ErrorResponse(
        error_code="INTERNAL_ERROR", message="An unexpected error occurred", correlation_id=cid
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def ready(session: Annotated[Session, Depends(get_db_session)]) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.get("/version")
async def version() -> dict[str, str]:
    git_sha = "unknown"
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        pass

    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "git_sha": git_sha,
        "environment": settings.app_env,
    }


@app.get("/metrics")
async def metrics():
    return metrics_response()


@app.post("/documents/ingest", response_model=IngestResponse)
async def ingest_documents_route(
    payload: IngestRequest, session: Annotated[Session, Depends(get_db_session)]
) -> IngestResponse:
    summary = ingest_documents(session, payload.documents)
    return IngestResponse(
        documents_ingested=summary.documents_ingested, chunks_ingested=summary.chunks_ingested
    )


@app.post("/qa", response_model=QaResponse)
async def qa_route(
    payload: QaRequest, session: Annotated[Session, Depends(get_db_session)]
) -> QaResponse:
    result = answer_question(
        session,
        payload.question,
        top_k=payload.top_k,
        ticker=payload.ticker,
        source=payload.source,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    return QaResponse(
        answer=result.answer,
        confidence=result.confidence,
        answer_provider=result.answer_provider,
        citations=[
            QaCitation(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                source=c.source,
                ticker=c.ticker,
                published_at=c.published_at,
                excerpt=c.excerpt,
                score=c.score,
            )
            for c in result.citations
        ],
    )


@app.post("/market/snapshots/fetch", response_model=MarketIngestResponse)
async def fetch_market_snapshots() -> MarketIngestResponse:
    result = run_market_snapshot_job()
    return MarketIngestResponse(records_processed=result.records_processed, details=result.details)


@app.get("/market/snapshots", response_model=list[MarketSnapshotResponse])
async def list_market_snapshots(
    session: Annotated[Session, Depends(get_db_session)],
    ticker: str | None = None,
    limit: int = 50,
) -> list[MarketSnapshotResponse]:
    safe_limit = min(max(limit, 1), 500)
    stmt = select(MarketPriceSnapshot)
    if ticker:
        stmt = stmt.where(MarketPriceSnapshot.ticker == ticker.upper())
    stmt = stmt.order_by(desc(MarketPriceSnapshot.ts_utc)).limit(safe_limit)
    rows = session.scalars(stmt).all()
    return [
        MarketSnapshotResponse(
            ticker=row.ticker,
            interval=row.interval,
            ts_utc=row.ts_utc,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
            source=row.source,
        )
        for row in rows
    ]


@app.post("/qa/evaluate", response_model=QaEvalResponse)
async def qa_evaluate_route(
    payload: QaEvalRequest, session: Annotated[Session, Depends(get_db_session)]
) -> QaEvalResponse:
    summary = evaluate_qa_cases(
        session,
        [
            QaEvalCase(
                question=case.question,
                top_k=case.top_k,
                ticker=case.ticker,
                source=case.source,
                date_from=case.date_from,
                date_to=case.date_to,
                min_citations=case.min_citations,
                min_confidence=case.min_confidence,
            )
            for case in payload.cases
        ],
    )
    return QaEvalResponse(
        total_cases=summary.total_cases,
        pass_rate=summary.pass_rate,
        citation_coverage=summary.citation_coverage,
        avg_confidence=summary.avg_confidence,
        cases=[
            QaEvalCaseResponse(
                question=item.question,
                confidence=item.confidence,
                citation_count=item.citation_count,
                passed=item.passed,
                reasons=item.reasons,
            )
            for item in summary.cases
        ],
    )


@app.post("/signals/sentiment/compute", response_model=SentimentComputeResponse)
async def compute_sentiment_route(
    payload: SentimentComputeRequest, session: Annotated[Session, Depends(get_db_session)]
) -> SentimentComputeResponse:
    result = compute_daily_sentiment_signals(
        session,
        ticker=payload.ticker,
        source=payload.source,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    return SentimentComputeResponse(
        rows_written=result.rows_written,
        tickers_processed=result.tickers_processed,
        provider_counts=result.provider_counts,
    )


@app.post("/qa/chunking/benchmark", response_model=ChunkingBenchmarkResponse)
async def chunking_benchmark_route(payload: ChunkingBenchmarkRequest) -> ChunkingBenchmarkResponse:
    summary = benchmark_chunkers(
        [
            ChunkingBenchmarkCase(question=case.question, content=case.content)
            for case in payload.cases
        ],
        threshold=payload.threshold,
    )
    return ChunkingBenchmarkResponse(
        threshold=summary.threshold,
        winner=summary.winner,
        metrics=[
            ChunkingBenchmarkMetricsResponse(
                provider=item.provider,
                avg_best_overlap=item.avg_best_overlap,
                pass_rate=item.pass_rate,
                avg_chunks_per_case=item.avg_chunks_per_case,
                avg_chunk_chars=item.avg_chunk_chars,
                runtime_ms=item.runtime_ms,
            )
            for item in summary.metrics
        ],
    )
