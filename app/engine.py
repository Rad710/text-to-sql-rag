"""The RAG vector store: a thin ChromaDB wrapper.

Holds the three corpus collections, seeds them idempotently from :func:`app.corpus.build_corpus`,
and answers low-level nearest-neighbour queries. The higher-level 4-tier ``search_schema`` merge is
built on top of this in task 0006. ChromaDB is imported lazily and used with **precomputed
embeddings** (no ONNX model, no network); telemetry is disabled.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.corpus import COLLECTIONS, CorpusItem
from app.embeddings import Embedder, get_embedder


@dataclass(frozen=True, slots=True)
class QueryHit:
    id: str
    document: str
    metadata: dict[str, Any]
    distance: float


class RagStore:
    """ChromaDB-backed store for the RAG corpus."""

    def __init__(self, path: str | None = None, embedder: Embedder | None = None) -> None:
        self._path = path or get_settings().chroma_path
        self._embedder = embedder or get_embedder()
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.PersistentClient(
                path=self._path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _collection(self, name: str) -> Any:
        return self._get_client().get_or_create_collection(
            name, metadata={"hnsw:space": "cosine"}, embedding_function=None
        )

    def sync_corpus(self, items: list[CorpusItem]) -> dict[str, dict[str, int]]:
        """Reconcile each collection with ``items``: add new, prune removed, skip unchanged."""
        by_collection: dict[str, list[CorpusItem]] = defaultdict(list)
        for item in items:
            by_collection[item.collection].append(item)

        stats: dict[str, dict[str, int]] = {}
        for name in COLLECTIONS:
            collection = self._collection(name)
            desired = {item.id: item for item in by_collection.get(name, [])}
            existing = set(collection.get()["ids"])

            to_add = [item_id for item_id in desired if item_id not in existing]
            to_delete = [item_id for item_id in existing if item_id not in desired]

            if to_add:
                add_items = [desired[item_id] for item_id in to_add]
                collection.add(
                    ids=to_add,
                    documents=[item.text for item in add_items],
                    embeddings=self._embedder.embed([item.text for item in add_items]),
                    metadatas=[item.metadata for item in add_items],
                )
            if to_delete:
                collection.delete(ids=to_delete)

            stats[name] = {
                "added": len(to_add),
                "deleted": len(to_delete),
                "unchanged": len(desired) - len(to_add),
            }
        return stats

    def query(self, collection: str, text: str, n_results: int = 5) -> list[QueryHit]:
        """Return the ``n_results`` nearest items in ``collection`` to ``text``."""
        col = self._collection(collection)
        count = col.count()
        if count == 0:
            return []
        result = col.query(
            query_embeddings=self._embedder.embed([text]),
            n_results=min(n_results, count),
            include=["documents", "metadatas", "distances"],
        )
        hits: list[QueryHit] = []
        for item_id, doc, meta, dist in zip(
            result["ids"][0],
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
            strict=True,
        ):
            hits.append(QueryHit(id=item_id, document=doc, metadata=meta, distance=dist))
        return hits
