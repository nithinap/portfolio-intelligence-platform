from src.common.settings import get_settings


def test_settings_load_defaults():
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.app_name == "finance-lm"
    assert settings.database_url.startswith("sqlite")
