"""Per-key request rate limiting — a small, pure, in-memory fixed-window limiter.

Kept dependency-free and clock-injected so the decision logic unit-tests without FastAPI, a real
clock, Redis, or a DB (mirrors the project's pure-core rule in CLAUDE.md). The API layer keys it by
authenticated user id on ``/chat`` (decision 0010) and turns a denial into a ``429`` + Retry-After.

Two independent fixed windows guard each key: a per-minute rate (anti-hammering) and an optional
per-day cap (per-account cost ceiling for the real-LLM deploy; ``0`` disables it). State is in RAM,
so it is per-process and resets on restart — sufficient for a single-instance demo deploy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

_MINUTE = 60
_DAY = 86_400


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    """Outcome of one limiter check."""

    ok: bool
    retry_after: int = 0  # seconds until the exceeded window rolls over
    scope: str = ""  # "minute" | "day" — which limit tripped (for the message)


@dataclass
class _Window:
    index: int  # which fixed window (floor(now / size)) the count belongs to
    count: int


@dataclass
class RateLimiter:
    """A fixed-window limiter: at most ``per_minute`` hits/60s and ``per_day`` hits/day per key.

    ``per_day == 0`` disables the daily cap. Checks are *check-then-count*: a denied request is not
    counted, so a blocked key's counter never grows past the limit and ``retry_after`` is just the
    time left in the tripped window.
    """

    per_minute: int
    per_day: int = 0
    _minute: dict[str, _Window] = field(default_factory=dict, repr=False)
    _day: dict[str, _Window] = field(default_factory=dict, repr=False)

    @staticmethod
    def _count(store: dict[str, _Window], key: str, index: int) -> int:
        """Current count for ``key`` in window ``index`` (resetting a stale window to 0)."""
        w = store.get(key)
        if w is None or w.index != index:
            return 0
        return w.count

    @staticmethod
    def _bump(store: dict[str, _Window], key: str, index: int) -> None:
        w = store.get(key)
        if w is None or w.index != index:
            store[key] = _Window(index=index, count=1)
        else:
            w.count += 1

    def check(self, key: str, now: float) -> RateLimitResult:
        """Allow or deny one request for ``key`` at time ``now`` (epoch seconds)."""
        minute_idx = int(now // _MINUTE)
        if self._count(self._minute, key, minute_idx) >= self.per_minute:
            return RateLimitResult(False, _MINUTE - int(now % _MINUTE), "minute")

        day_idx = int(now // _DAY)
        if self.per_day > 0 and self._count(self._day, key, day_idx) >= self.per_day:
            return RateLimitResult(False, _DAY - int(now % _DAY), "day")

        self._bump(self._minute, key, minute_idx)
        if self.per_day > 0:
            self._bump(self._day, key, day_idx)
        return RateLimitResult(True)
