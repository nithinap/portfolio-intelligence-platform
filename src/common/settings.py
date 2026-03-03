from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="finance-lm", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(
        default="sqlite:///./data/processed/finance_lm.db", alias="DATABASE_URL"
    )
    vector_db_provider: str = Field(default="pgvector", alias="VECTOR_DB_PROVIDER")
    vector_db_url: str | None = Field(default=None, alias="VECTOR_DB_URL")
    qa_answer_provider: str = Field(default="deterministic", alias="QA_ANSWER_PROVIDER")
    qa_openai_model: str = Field(default="gpt-4o-mini", alias="QA_OPENAI_MODEL")
    qa_openai_base_url: str = Field(default="https://api.openai.com/v1", alias="QA_OPENAI_BASE_URL")
    qa_openai_timeout_seconds: int = Field(default=20, alias="QA_OPENAI_TIMEOUT_SECONDS")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embedding_provider: str = Field(default="sparse-local", alias="EMBEDDING_PROVIDER")
    retrieval_provider: str = Field(default="sparse-local", alias="RETRIEVAL_PROVIDER")
    chunker_provider: str = Field(default="simple", alias="CHUNKER_PROVIDER")
    chunk_max_chars: int = Field(default=800, alias="CHUNK_MAX_CHARS")
    chunk_overlap_chars: int = Field(default=120, alias="CHUNK_OVERLAP_CHARS")
    chunk_max_tokens: int = Field(default=180, alias="CHUNK_MAX_TOKENS")
    chunk_overlap_tokens: int = Field(default=30, alias="CHUNK_OVERLAP_TOKENS")
    market_data_provider: str = Field(default="stub", alias="MARKET_DATA_PROVIDER")
    market_data_tickers: str = Field(default="AAPL,MSFT,NVDA", alias="MARKET_DATA_TICKERS")
    market_data_lookback_days: int = Field(default=5, alias="MARKET_DATA_LOOKBACK_DAYS")


def _load_yaml_profile(app_env: str) -> dict[str, Any]:
    cfg_path = Path("configs") / f"{app_env}.yaml"
    if not cfg_path.exists():
        return {}
    with cfg_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    base = Settings()
    env = base.app_env
    yaml_cfg = _load_yaml_profile(env)
    mapped = {
        "APP_ENV": yaml_cfg.get("app_env"),
        "LOG_LEVEL": yaml_cfg.get("log_level"),
        "DATABASE_URL": yaml_cfg.get("database_url"),
        "VECTOR_DB_PROVIDER": yaml_cfg.get("vector_db_provider"),
        "VECTOR_DB_URL": yaml_cfg.get("vector_db_url"),
        "QA_ANSWER_PROVIDER": yaml_cfg.get("qa_answer_provider"),
        "QA_OPENAI_MODEL": yaml_cfg.get("qa_openai_model"),
        "QA_OPENAI_BASE_URL": yaml_cfg.get("qa_openai_base_url"),
        "QA_OPENAI_TIMEOUT_SECONDS": yaml_cfg.get("qa_openai_timeout_seconds"),
        "EMBEDDING_PROVIDER": yaml_cfg.get("embedding_provider"),
        "RETRIEVAL_PROVIDER": yaml_cfg.get("retrieval_provider"),
        "CHUNKER_PROVIDER": yaml_cfg.get("chunker_provider"),
        "CHUNK_MAX_CHARS": yaml_cfg.get("chunk_max_chars"),
        "CHUNK_OVERLAP_CHARS": yaml_cfg.get("chunk_overlap_chars"),
        "CHUNK_MAX_TOKENS": yaml_cfg.get("chunk_max_tokens"),
        "CHUNK_OVERLAP_TOKENS": yaml_cfg.get("chunk_overlap_tokens"),
        "MARKET_DATA_PROVIDER": yaml_cfg.get("market_data_provider"),
        "MARKET_DATA_TICKERS": yaml_cfg.get("market_data_tickers"),
        "MARKET_DATA_LOOKBACK_DAYS": yaml_cfg.get("market_data_lookback_days"),
    }
    merged = {k: v for k, v in mapped.items() if v is not None and os.getenv(k) is None}
    return Settings(**merged)
