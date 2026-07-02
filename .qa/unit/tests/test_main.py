# Categoria: integration
# File sorgente: backend/main.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-17

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


def test_app_starts_and_returns_health(test_client):
    resp = test_client.get("/api/health/")
    assert resp.status_code == 200


def test_cors_headers_present(test_client):
    resp = test_client.get("/api/health/", headers={"Origin": "http://localhost:5173"})
    assert resp.status_code == 200
    # CORS header should be present regardless of origin
    assert "access-control-allow-origin" in resp.headers
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_upload_endpoint_exists(test_client):
    resp = test_client.post("/api/analysis/upload")
    # L'endpoint esiste ma rifiuta la richiesta perché manca il file
    assert resp.status_code == 422, f"Expected 422 (validation error), got {resp.status_code}"
    body = resp.json()
    assert "detail" in body
    details = body["detail"] if isinstance(body["detail"], list) else [body["detail"]]
    assert any("file" in str(d).lower() for d in details)


def test_analysis_endpoint_requires_body(test_client):
    resp = test_client.post("/api/analysis/analyze/fake-id")
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body


def test_analysis_rejects_cleaning_actions_object(test_client):
    resp = test_client.post(
        "/api/analysis/analyze/fake-id",
        json={"cleaning_actions": {}},
    )
    assert resp.status_code == 422
    # Deve rifiutare un oggetto quando si aspetta una lista
    body = resp.json()
    assert "detail" in body
    assert len(body["detail"]) >= 1


def test_analysis_accepts_cleaning_actions_list(test_client):
    resp = test_client.post(
        "/api/analysis/analyze/fake-id",
        json={"cleaning_actions": []},
    )
    # La lista vuota è valida, ma file_id non esiste → 404
    assert resp.status_code == 404
    assert isinstance(resp.json()["detail"], str)
