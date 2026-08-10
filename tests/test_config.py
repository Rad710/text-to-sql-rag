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
    monkeypatch.setenv("DB_PORT", "3307")
    get_settings.cache_clear()
    s = get_settings()
    assert s.llm_mode == "openai"
    assert s.is_mock is False
    assert s.db_port == 3307
    get_settings.cache_clear()


def test_unknown_llm_mode_falls_back_to_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODE", "banana")
    get_settings.cache_clear()
    assert get_settings().llm_mode == "mock"
    get_settings.cache_clear()
