from __future__ import annotations

import uuid

from src.common.db import SessionLocal
from src.common.settings import get_settings
from src.data_ingestion.pipelines.document_ingestion import ingest_documents
from src.data_ingestion.schemas import IngestDocumentInput
from src.rag.qa import answer_question


def test_qa_default_provider_is_deterministic():
    get_settings.cache_clear()
    source = f"qa-provider-{uuid.uuid4().hex[:8]}"
    with SessionLocal() as session:
        ingest_documents(
            session,
            [
                IngestDocumentInput(
                    source=source,
                    ticker="AAPL",
                    title="AAPL growth",
                    content="Apple showed strong growth and improved operating margin.",
                )
            ],
        )
        result = answer_question(
            session,
            "What does evidence say about Apple growth?",
            ticker="AAPL",
            source=source,
        )
    assert result.answer_provider == "deterministic"
    assert len(result.citations) >= 1


def test_qa_openai_provider_falls_back_without_key(monkeypatch):
    monkeypatch.setenv("QA_ANSWER_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()

    source = f"qa-openai-fallback-{uuid.uuid4().hex[:8]}"
    with SessionLocal() as session:
        ingest_documents(
            session,
            [
                IngestDocumentInput(
                    source=source,
                    ticker="MSFT",
                    title="MSFT cloud",
                    content="Cloud demand accelerated and enterprise adoption remained strong.",
                )
            ],
        )
        result = answer_question(
            session,
            "What is the cloud demand trend?",
            ticker="MSFT",
            source=source,
        )
    assert result.answer_provider == "deterministic-fallback"
    assert len(result.citations) >= 1
    get_settings.cache_clear()
