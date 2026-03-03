from src.signals.sentiment_scoring import score_with_fallback


def test_lexicon_sentiment_scoring_returns_positive_value():
    result = score_with_fallback(
        "Strong growth accelerated and guidance improved.",
        primary_provider="lexicon",
        openai_api_key=None,
        openai_model="gpt-4o-mini",
        openai_base_url="https://api.openai.com/v1",
        openai_timeout_seconds=20,
    )
    assert result.provider_used == "lexicon"
    assert result.value > 0


def test_openai_sentiment_scoring_falls_back_without_key():
    result = score_with_fallback(
        "Demand weakened and downside risk increased.",
        primary_provider="openai",
        openai_api_key="",
        openai_model="gpt-4o-mini",
        openai_base_url="https://api.openai.com/v1",
        openai_timeout_seconds=20,
    )
    assert result.provider_used == "lexicon-fallback"
    assert result.value < 0
