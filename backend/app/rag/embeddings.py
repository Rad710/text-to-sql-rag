"""Text embeddings.

The default :class:`OfflineEmbedder` is deterministic and dependency-free (feature-hashing of words
+ character trigrams, L2-normalized) — retrieval runs in mock mode and CI with **no model download
and no network**. It is pure and unit-testable. A real transformer embedder plugs in at
:func:`get_embedder` when real LLM mode arrives (deferred — see task 0005 discussion).
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


_TOKEN_RE = re.compile(r"[a-z0-9_]+")


class OfflineEmbedder:
    """Deterministic hashing embedder. Same text → same vector; related texts → higher cosine."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in self._features(text):
            for bucket in self._hash_buckets(token):
                vec[bucket % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]

    @staticmethod
    def _features(text: str) -> list[str]:
        words = _TOKEN_RE.findall(text.lower())
        trigrams = [w[i : i + 3] for w in words for i in range(max(1, len(w) - 2))]
        return words + trigrams

    @staticmethod
    def _hash_buckets(token: str) -> tuple[int, int]:
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        return (
            int.from_bytes(digest[0:4], "big"),
            int.from_bytes(digest[4:8], "big"),
        )


def get_embedder() -> Embedder:
    """Return the process embedder. Offline/deterministic by default (see module docstring)."""
    return OfflineEmbedder()
