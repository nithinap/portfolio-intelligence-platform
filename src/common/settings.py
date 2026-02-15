from __future__ import annotations

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


def _load_yaml_profile(app_env: str) -> dict[str, Any]:
    cfg_path = Path("configs") / f"{app_env}.yaml"
    if not cfg_path.exists():
        return {}
    with cfg_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env = Settings().app_env
    yaml_cfg = _load_yaml_profile(env)
    mapped = {
        "APP_ENV": yaml_cfg.get("app_env"),
        "LOG_LEVEL": yaml_cfg.get("log_level"),
        "DATABASE_URL": yaml_cfg.get("database_url"),
        "VECTOR_DB_PROVIDER": yaml_cfg.get("vector_db_provider"),
        "VECTOR_DB_URL": yaml_cfg.get("vector_db_url"),
    }
    merged = {k: v for k, v in mapped.items() if v is not None}
    return Settings(**merged)
