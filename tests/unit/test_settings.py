from src.common.settings import get_settings


def test_settings_load_defaults():
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.app_name == "finance-lm"
    assert settings.database_url.startswith("sqlite")
    assert settings.market_data_provider in {"stub", "yahoo", "yfinance", "yahoo-chart"}
    assert settings.embedding_provider in {"sparse-local", "local-sparse", "sparse"}
    assert settings.retrieval_provider in {"sparse-local", "local-sparse", "sparse", "lexical"}


def test_env_overrides_yaml(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "yfinance")
    monkeypatch.setenv("RETRIEVAL_PROVIDER", "lexical")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.market_data_provider == "yfinance"
    assert settings.retrieval_provider == "lexical"
