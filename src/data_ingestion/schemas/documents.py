from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class IngestDocumentInput(BaseModel):
    source: str = Field(min_length=1, max_length=50)
    ticker: str | None = Field(default=None, max_length=16)
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1)
    published_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)
