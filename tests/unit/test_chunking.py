from src.rag.chunking import SimpleChunker, TokenChunker, get_chunker


def test_simple_chunker_splits_by_chars():
    chunker = SimpleChunker(max_chars=30, overlap_chars=5)
    text = "one two three four five six seven eight nine ten eleven twelve"
    chunks = chunker.chunk(document_id=1, text=text)
    assert len(chunks) >= 2
    assert chunks[0].metadata["chunker"] == "simple"


def test_token_chunker_splits_by_tokens():
    chunker = TokenChunker(max_tokens=6, overlap_tokens=2)
    text = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
    chunks = chunker.chunk(document_id=2, text=text)
    assert len(chunks) >= 2
    assert chunks[0].metadata["chunker"] == "token"
    first_words = chunks[0].content.split(" ")
    assert len(first_words) <= 6


def test_get_chunker_selects_token_variant():
    chunker = get_chunker("token")
    assert isinstance(chunker, TokenChunker)
