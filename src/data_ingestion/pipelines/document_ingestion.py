from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.core.models import Document, DocumentChunk, EmbeddingMetadata
from src.data_ingestion.schemas import IngestDocumentInput
from src.rag.chunking import chunk_text


@dataclass
class IngestionSummary:
    documents_ingested: int
    chunks_ingested: int


def ingest_documents(session: Session, docs: list[IngestDocumentInput]) -> IngestionSummary:
    docs_count = 0
    chunks_count = 0

    for payload in docs:
        doc = Document(
            source=payload.source,
            ticker=payload.ticker,
            title=payload.title,
            content=payload.content,
            published_at=payload.published_at,
        )
        session.add(doc)
        session.flush()
        docs_count += 1

        chunks = chunk_text(document_id=doc.id, text=payload.content)
        for chunk in chunks:
            session.add(
                DocumentChunk(
                    document_id=doc.id,
                    chunk_id=chunk.chunk_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    source=payload.source,
                    ticker=payload.ticker,
                    published_at=payload.published_at,
                    metadata_json={**payload.metadata, **chunk.metadata},
                )
            )
            session.add(
                EmbeddingMetadata(
                    document_id=doc.id,
                    chunk_id=chunk.chunk_id,
                    vector_provider="stub-lexical",
                    model_name="keyword-overlap-v1",
                    payload={"char_count": len(chunk.content)},
                )
            )
            chunks_count += 1

    session.commit()
    return IngestionSummary(documents_ingested=docs_count, chunks_ingested=chunks_count)
