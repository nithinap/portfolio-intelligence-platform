from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Chunk:
    chunk_id: str
    chunk_index: int
    content: str
    metadata: dict[str, str | int]


class Chunker(Protocol):
    def chunk(self, document_id: int, text: str) -> list[Chunk]:
        ...


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _build_chunk(document_id: int, idx: int, body: str, metadata: dict[str, str | int]) -> Chunk:
    digest = hashlib.sha1(f"{document_id}:{idx}:{body}".encode()).hexdigest()[:24]
    return Chunk(
        chunk_id=f"doc{document_id}_{digest}",
        chunk_index=idx,
        content=body,
        metadata=metadata,
    )


class SimpleChunker:
    def __init__(self, max_chars: int = 800, overlap_chars: int = 120):
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk(self, document_id: int, text: str) -> list[Chunk]:
        clean = _clean_text(text)
        if not clean:
            return []

        chunks: list[Chunk] = []
        start = 0
        idx = 0
        while start < len(clean):
            end = min(len(clean), start + self.max_chars)
            body = clean[start:end].strip()
            chunks.append(
                _build_chunk(
                    document_id,
                    idx,
                    body,
                    {"chunker": "simple", "start_char": start, "end_char": end},
                )
            )
            if end >= len(clean):
                break
            start = max(0, end - self.overlap_chars)
            idx += 1
        return chunks


class TokenChunker:
    def __init__(self, max_tokens: int = 180, overlap_tokens: int = 30):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk(self, document_id: int, text: str) -> list[Chunk]:
        clean = _clean_text(text)
        if not clean:
            return []
        tokens = clean.split(" ")
        if not tokens:
            return []

        chunks: list[Chunk] = []
        start = 0
        idx = 0
        while start < len(tokens):
            end = min(len(tokens), start + self.max_tokens)
            body = " ".join(tokens[start:end]).strip()
            chunks.append(
                _build_chunk(
                    document_id,
                    idx,
                    body,
                    {"chunker": "token", "start_token": start, "end_token": end},
                )
            )
            if end >= len(tokens):
                break
            start = max(0, end - self.overlap_tokens)
            idx += 1
        return chunks


def get_chunker(
    provider_name: str,
    *,
    max_chars: int = 800,
    overlap_chars: int = 120,
    max_tokens: int = 180,
    overlap_tokens: int = 30,
) -> Chunker:
    normalized = provider_name.strip().lower()
    if normalized in {"token", "token-local"}:
        return TokenChunker(max_tokens=max_tokens, overlap_tokens=overlap_tokens)
    return SimpleChunker(max_chars=max_chars, overlap_chars=overlap_chars)


def chunk_text(
    document_id: int,
    text: str,
    *,
    max_chars: int = 800,
    overlap_chars: int = 120,
) -> list[Chunk]:
    # Backwards-compatible helper used by older call sites and tests.
    chunker = SimpleChunker(max_chars=max_chars, overlap_chars=overlap_chars)
    return chunker.chunk(document_id, text)
