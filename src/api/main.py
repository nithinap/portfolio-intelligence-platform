from __future__ import annotations

import subprocess
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.common.bootstrap import bootstrap_database
from src.common.db import get_db_session
from src.common.errors import ErrorResponse
from src.common.logging import configure_logging, get_correlation_id, get_logger, set_correlation_id
from src.common.observability import MetricsMiddleware, metrics_response, setup_tracing
from src.common.settings import get_settings
from src.data_ingestion.pipelines.document_ingestion import ingest_documents
from src.data_ingestion.schemas import IngestDocumentInput
from src.rag.qa import answer_question

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
    citations: list[QaCitation]


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
