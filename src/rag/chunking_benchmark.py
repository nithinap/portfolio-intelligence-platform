from __future__ import annotations

import re
from dataclasses import dataclass
from time import perf_counter

from src.rag.chunking import get_chunker


@dataclass
class ChunkingBenchmarkCase:
    question: str
    content: str


@dataclass
class ChunkingBenchmarkMetrics:
    provider: str
    avg_best_overlap: float
    pass_rate: float
    avg_chunks_per_case: float
    avg_chunk_chars: float
    runtime_ms: float


@dataclass
class ChunkingBenchmarkSummary:
    threshold: float
    metrics: list[ChunkingBenchmarkMetrics]
    winner: str


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z0-9]{3,}", text.lower())}


def _best_overlap(question: str, chunks: list[str]) -> float:
    question_terms = _tokenize(question)
    if not question_terms:
        return 0.0
    best = 0.0
    for chunk in chunks:
        chunk_terms = _tokenize(chunk)
        overlap = len(question_terms & chunk_terms) / len(question_terms)
        best = max(best, overlap)
    return best


def _benchmark_provider(
    provider: str,
    cases: list[ChunkingBenchmarkCase],
    threshold: float,
) -> ChunkingBenchmarkMetrics:
    if not cases:
        return ChunkingBenchmarkMetrics(
            provider=provider,
            avg_best_overlap=0.0,
            pass_rate=0.0,
            avg_chunks_per_case=0.0,
            avg_chunk_chars=0.0,
            runtime_ms=0.0,
        )

    chunker = get_chunker(provider)
    t0 = perf_counter()
    best_scores: list[float] = []
    chunk_counts: list[int] = []
    chunk_sizes: list[int] = []

    for idx, case in enumerate(cases, start=1):
        chunks = chunker.chunk(document_id=idx, text=case.content)
        chunk_texts = [chunk.content for chunk in chunks]
        best_scores.append(_best_overlap(case.question, chunk_texts))
        chunk_counts.append(len(chunk_texts))
        chunk_sizes.extend([len(text) for text in chunk_texts])

    elapsed_ms = (perf_counter() - t0) * 1000.0
    pass_count = sum(1 for score in best_scores if score >= threshold)
    avg_best_overlap = sum(best_scores) / len(best_scores)
    avg_chunks = sum(chunk_counts) / len(chunk_counts)
    avg_chunk_chars = (sum(chunk_sizes) / len(chunk_sizes)) if chunk_sizes else 0.0

    return ChunkingBenchmarkMetrics(
        provider=provider,
        avg_best_overlap=round(avg_best_overlap, 3),
        pass_rate=round(pass_count / len(best_scores), 3),
        avg_chunks_per_case=round(avg_chunks, 3),
        avg_chunk_chars=round(avg_chunk_chars, 1),
        runtime_ms=round(elapsed_ms, 2),
    )


def benchmark_chunkers(
    cases: list[ChunkingBenchmarkCase], *, threshold: float = 0.35
) -> ChunkingBenchmarkSummary:
    simple = _benchmark_provider("simple", cases, threshold)
    token = _benchmark_provider("token", cases, threshold)
    winner = _pick_winner(simple, token)
    return ChunkingBenchmarkSummary(
        threshold=threshold,
        metrics=[simple, token],
        winner=winner,
    )


def _pick_winner(
    simple: ChunkingBenchmarkMetrics, token: ChunkingBenchmarkMetrics
) -> str:
    if simple.pass_rate > token.pass_rate:
        return "simple"
    if token.pass_rate > simple.pass_rate:
        return "token"
    if simple.avg_best_overlap > token.avg_best_overlap:
        return "simple"
    if token.avg_best_overlap > simple.avg_best_overlap:
        return "token"
    return "simple" if simple.runtime_ms <= token.runtime_ms else "token"
