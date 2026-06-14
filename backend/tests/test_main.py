# Categoria: integration
# File sorgente: backend/main.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_app_starts_and_returns_health():
    resp = client.get("/api/health/")
    assert resp.status_code == 200


def test_cors_headers_present():
    resp = client.get("/api/health/", headers={"Origin": "http://localhost:5173"})
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers


def test_upload_endpoint_exists():
    resp = client.post("/api/analysis/upload")
    assert resp.status_code in (405, 422, 413, 400)


def test_analysis_endpoint_requires_body():
    resp = client.post("/api/analysis/analyze/fake-id")
    assert resp.status_code == 422


def test_analysis_rejects_cleaning_actions_object():
    resp = client.post(
        "/api/analysis/analyze/fake-id",
        json={"cleaning_actions": {}},
    )
    assert resp.status_code == 422


def test_analysis_accepts_cleaning_actions_list():
    resp = client.post(
        "/api/analysis/analyze/fake-id",
        json={"cleaning_actions": []},
    )
    assert resp.status_code == 404
