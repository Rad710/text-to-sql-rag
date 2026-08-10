"""The FastAPI skeleton is runnable: health check and a mock-mode chat stub."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_stub_echoes_in_mock_mode() -> None:
    resp = client.post("/chat", json={"question": "cuánto facturamos?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "mock"
    assert "cuánto facturamos?" in body["answer"]


def test_chat_requires_question() -> None:
    resp = client.post("/chat", json={})
    assert resp.status_code == 422
