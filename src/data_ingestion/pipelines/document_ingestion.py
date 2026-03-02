from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.common.settings import get_settings
from src.core.models import Document, DocumentChunk, EmbeddingMetadata
from src.data_ingestion.schemas import IngestDocumentInput
from src.rag.chunking import chunk_text
from src.rag.embeddings import get_embedding_provider

settings = get_settings()


@dataclass
class IngestionSummary:
    documents_ingested: int
    chunks_ingested: int


def ingest_documents(session: Session, docs: list[IngestDocumentInput]) -> IngestionSummary:
    docs_count = 0
    chunks_count = 0
    embedding_provider = get_embedding_provider(settings.embedding_provider)

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
                    vector_provider=settings.embedding_provider,
                    model_name="sparse-termfreq-v1",
                    payload={
                        "char_count": len(chunk.content),
                        "embedding": embedding_provider.embed(chunk.content),
                    },
                )
            )
            chunks_count += 1

    session.commit()
    return IngestionSummary(documents_ingested=docs_count, chunks_ingested=chunks_count)
