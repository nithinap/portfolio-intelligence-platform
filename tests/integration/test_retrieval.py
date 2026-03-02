from __future__ import annotations

import uuid

from sqlalchemy import select

from src.common.db import SessionLocal
from src.common.settings import get_settings
from src.core.models import EmbeddingMetadata
from src.data_ingestion.pipelines.document_ingestion import ingest_documents
from src.data_ingestion.schemas import IngestDocumentInput
from src.rag.retrieval import retrieve_chunks


def test_ingestion_stores_sparse_embedding_and_retrieval_uses_it(monkeypatch):
    test_source = f"retrieval-test-{uuid.uuid4().hex[:8]}"
    with SessionLocal() as session:
        ingest_documents(
            session,
            [
                IngestDocumentInput(
                    source=test_source,
                    ticker="NVDA",
                    title="GPU demand",
                    content=(
                        "NVIDIA data center demand remained strong with AI workloads expanding "
                        "across cloud customers."
                    ),
                )
            ],
        )
        row = session.scalars(
            select(EmbeddingMetadata).order_by(EmbeddingMetadata.id.desc())
        ).first()
        assert row is not None
        assert isinstance(row.payload.get("embedding"), dict)
        assert len(row.payload.get("embedding", {})) > 0

    monkeypatch.setenv("RETRIEVAL_PROVIDER", "sparse-local")
    get_settings.cache_clear()
    with SessionLocal() as session:
        chunks = retrieve_chunks(
            session,
            "What is happening with NVIDIA AI cloud demand?",
            top_k=3,
            ticker="NVDA",
            source=test_source,
        )
        assert len(chunks) >= 1
        assert chunks[0].score > 0


def test_retrieval_lexical_mode_fallback(monkeypatch):
    test_source = f"retrieval-lexical-{uuid.uuid4().hex[:8]}"
    with SessionLocal() as session:
        ingest_documents(
            session,
            [
                IngestDocumentInput(
                    source=test_source,
                    ticker="AAPL",
                    title="AAPL margins",
                    content="Apple margins improved and revenue guidance increased.",
                )
            ],
        )

    monkeypatch.setenv("RETRIEVAL_PROVIDER", "lexical")
    get_settings.cache_clear()
    with SessionLocal() as session:
        chunks = retrieve_chunks(
            session,
            "Apple margins and revenue guidance",
            top_k=3,
            ticker="AAPL",
            source=test_source,
        )
        assert len(chunks) >= 1
