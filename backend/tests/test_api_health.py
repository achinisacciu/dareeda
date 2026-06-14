# Categoria: integration
# File sorgente: backend/api/routes/health.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok():
    resp = client.get("/api/health/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "DAREEDA API"}


def test_health_endpoint_content_type():
    resp = client.get("/api/health/")
    assert resp.headers["content-type"] == "application/json"
