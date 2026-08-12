"""Settings behave as a frozen, mock-default, env-driven config."""

from __future__ import annotations

import dataclasses

import pytest

from app.config import Settings, get_settings


def test_defaults_to_mock_mode() -> None:
    s = Settings()
    assert s.llm_mode == "mock"
    assert s.is_mock is True


def test_settings_is_frozen() -> None:
    s = Settings()
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.llm_mode = "openai"  # type: ignore[misc]


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()


def test_env_overrides_are_applied(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODE", "openai")
    monkeypatch.setenv("QUERY_DB_PORT", "3307")
    get_settings.cache_clear()
    s = get_settings()
    assert s.llm_mode == "openai"
    assert s.is_mock is False
    assert s.query_db_port == 3307
    get_settings.cache_clear()


def test_app_database_url_assembled_from_parts() -> None:
    s = Settings(
        app_db_host="db.internal",
        app_db_port=6543,
        app_db_user="svc",
        app_db_password="p@ss/word",  # special chars must be percent-encoded
        app_db_name="appdb",
    )
    assert s.app_database_url == "postgresql+asyncpg://svc:p%40ss%2Fword@db.internal:6543/appdb"


def test_app_db_env_parts_are_applied(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in {
        "APP_DB_HOST": "pg.example.com",
        "APP_DB_PORT": "5544",
        "APP_DB_USER": "app",
        "APP_DB_PASSWORD": "app",
        "APP_DB_NAME": "prod_app",
    }.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    assert (
        get_settings().app_database_url
        == "postgresql+asyncpg://app:app@pg.example.com:5544/prod_app"
    )
    get_settings.cache_clear()


def test_unknown_llm_mode_falls_back_to_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODE", "banana")
    get_settings.cache_clear()
    assert get_settings().llm_mode == "mock"
    get_settings.cache_clear()


def test_demo_mode_is_the_default_with_no_daily_cap() -> None:
    s = Settings()
    assert s.deploy_mode == "demo"
    assert s.rate_limit_per_min == 60
    assert s.rate_limit_per_day == 0  # 0 = no daily ceiling in demo


def test_live_mode_sets_strict_rate_limit_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPLOY_MODE", "live")
    get_settings.cache_clear()
    s = get_settings()
    assert s.deploy_mode == "live"
    assert (s.rate_limit_per_min, s.rate_limit_per_day) == (20, 100)
    get_settings.cache_clear()


def test_explicit_rate_limit_env_overrides_mode_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPLOY_MODE", "live")
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "5")
    monkeypatch.setenv("RATE_LIMIT_PER_DAY", "0")
    get_settings.cache_clear()
    s = get_settings()
    assert (s.rate_limit_per_min, s.rate_limit_per_day) == (5, 0)
    get_settings.cache_clear()
