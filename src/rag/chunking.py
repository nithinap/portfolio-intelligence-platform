from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: str
    chunk_index: int
    content: str
    metadata: dict[str, str | int]


def chunk_text(
    document_id: int,
    text: str,
    *,
    max_chars: int = 800,
    overlap_chars: int = 120,
) -> list[Chunk]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []

    chunks: list[Chunk] = []
    start = 0
    idx = 0
    while start < len(clean):
        end = min(len(clean), start + max_chars)
        body = clean[start:end].strip()
        digest = hashlib.sha1(f"{document_id}:{idx}:{body}".encode()).hexdigest()[:24]
        chunks.append(
            Chunk(
                chunk_id=f"doc{document_id}_{digest}",
                chunk_index=idx,
                content=body,
                metadata={"start_char": start, "end_char": end},
            )
        )
        if end >= len(clean):
            break
        start = max(0, end - overlap_chars)
        idx += 1
    return chunks
