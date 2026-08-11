"""Unit tests for the pure fixed-window rate limiter (no clock, no FastAPI)."""

from __future__ import annotations

from app.ratelimit import RateLimiter


def test_allows_up_to_the_per_minute_limit_then_denies() -> None:
    limiter = RateLimiter(per_minute=3)
    now = 1000.0  # arbitrary epoch inside one minute window
    assert [limiter.check("u1", now).ok for _ in range(3)] == [True, True, True]
    denied = limiter.check("u1", now)
    assert denied.ok is False
    assert denied.scope == "minute"
    assert 0 < denied.retry_after <= 60


def test_window_rolls_over_after_a_minute() -> None:
    limiter = RateLimiter(per_minute=2)
    assert limiter.check("u1", 0.0).ok
    assert limiter.check("u1", 30.0).ok
    assert limiter.check("u1", 59.0).ok is False  # same minute → blocked
    assert limiter.check("u1", 60.0).ok is True  # next minute → fresh window


def test_keys_are_independent() -> None:
    limiter = RateLimiter(per_minute=1)
    assert limiter.check("a", 0.0).ok is True
    assert limiter.check("b", 0.0).ok is True  # different key, own budget
    assert limiter.check("a", 0.0).ok is False


def test_denied_requests_are_not_counted() -> None:
    # check-then-count: being blocked does not consume future budget beyond the window.
    limiter = RateLimiter(per_minute=1)
    assert limiter.check("u1", 0.0).ok is True
    assert limiter.check("u1", 10.0).ok is False
    assert limiter.check("u1", 20.0).ok is False
    assert limiter.check("u1", 60.0).ok is True  # window rolled; exactly one allowed again


def test_daily_cap_zero_means_unlimited_per_day() -> None:
    limiter = RateLimiter(per_minute=1000, per_day=0)
    # 5 minutes apart so the per-minute window never trips; the day cap is disabled.
    assert all(limiter.check("u1", i * 60.0).ok for i in range(10))


def test_daily_cap_trips_after_per_day_across_minutes() -> None:
    limiter = RateLimiter(per_minute=1000, per_day=3)
    assert [limiter.check("u1", i * 60.0).ok for i in range(3)] == [True, True, True]
    denied = limiter.check("u1", 3 * 60.0)  # 4th of the day, new minute window
    assert denied.ok is False
    assert denied.scope == "day"
    assert 0 < denied.retry_after <= 86_400


def test_daily_window_rolls_over_next_day() -> None:
    limiter = RateLimiter(per_minute=1000, per_day=1)
    assert limiter.check("u1", 0.0).ok is True
    assert limiter.check("u1", 3600.0).ok is False  # same day
    assert limiter.check("u1", 86_400.0).ok is True  # next day → fresh daily budget
