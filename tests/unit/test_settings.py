from src.common.settings import get_settings


def test_settings_load_defaults():
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.app_name == "finance-lm"
    assert settings.database_url.startswith("sqlite")
    assert settings.market_data_provider in {"stub", "yahoo", "yfinance", "yahoo-chart"}
    assert settings.embedding_provider in {"sparse-local", "local-sparse", "sparse"}
    assert settings.retrieval_provider in {"sparse-local", "local-sparse", "sparse", "lexical"}
    assert settings.qa_answer_provider in {"deterministic", "openai"}
    assert settings.qa_openai_model
    assert settings.qa_openai_base_url.startswith("https://")
    assert settings.qa_openai_timeout_seconds > 0
    assert settings.chunker_provider in {"simple", "token", "token-local"}
    assert settings.chunk_max_chars > 0
    assert settings.chunk_max_tokens > 0


def test_env_overrides_yaml(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "yfinance")
    monkeypatch.setenv("RETRIEVAL_PROVIDER", "lexical")
    monkeypatch.setenv("QA_ANSWER_PROVIDER", "openai")
    monkeypatch.setenv("CHUNKER_PROVIDER", "token")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.market_data_provider == "yfinance"
    assert settings.retrieval_provider == "lexical"
    assert settings.qa_answer_provider == "openai"
    assert settings.chunker_provider == "token"
