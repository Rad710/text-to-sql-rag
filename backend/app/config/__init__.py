"""Cross-cutting configuration + limits.

Groups the app-wide settings (``config``) and the per-user rate limiter (``ratelimit``) — both pure,
import-time-cheap, and shared across layers. Re-exported here so call sites keep the flat
``from app.config import get_settings`` / ``RateLimiter`` imports regardless of the internal split.
"""

from __future__ import annotations

from app.config.config import LlmMode, Settings, get_settings
from app.config.ratelimit import RateLimiter, RateLimitResult

__all__ = [
    "LlmMode",
    "RateLimiter",
    "RateLimitResult",
    "Settings",
    "get_settings",
]
