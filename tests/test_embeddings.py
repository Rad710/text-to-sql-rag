"""Pure tests for the deterministic offline embedder."""

from __future__ import annotations

import math

from app.rag.embeddings import OfflineEmbedder


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_deterministic_and_fixed_dim() -> None:
    emb = OfflineEmbedder(dim=128)
    v1 = emb.embed(["total revenue per route"])[0]
    v2 = emb.embed(["total revenue per route"])[0]
    assert v1 == v2
    assert len(v1) == 128


def test_l2_normalized() -> None:
    v = OfflineEmbedder().embed(["some freight text about drivers"])[0]
    assert math.isclose(math.sqrt(_dot(v, v)), 1.0, rel_tol=1e-9)


def test_empty_text_is_zero_vector() -> None:
    v = OfflineEmbedder(dim=64).embed([""])[0]
    assert v == [0.0] * 64


def test_related_text_is_closer_than_unrelated() -> None:
    emb = OfflineEmbedder()
    query = emb.embed(["total revenue per route"])[0]
    related = emb.embed(["revenue by route"])[0]
    unrelated = emb.embed(["driver truck plate registration"])[0]
    assert _dot(query, related) > _dot(query, unrelated)
