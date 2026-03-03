from src.rag.chunking_benchmark import ChunkingBenchmarkCase, benchmark_chunkers


def test_benchmark_chunkers_returns_two_providers():
    summary = benchmark_chunkers(
        [
            ChunkingBenchmarkCase(
                question="What is the trend in revenue growth?",
                content=(
                    "Revenue growth accelerated this quarter and guidance remained positive."
                ),
            ),
            ChunkingBenchmarkCase(
                question="How did margins perform?",
                content="Operating margins improved while costs remained controlled.",
            ),
        ],
        threshold=0.2,
    )
    assert summary.winner in {"simple", "token"}
    assert len(summary.metrics) == 2
    providers = {m.provider for m in summary.metrics}
    assert providers == {"simple", "token"}
