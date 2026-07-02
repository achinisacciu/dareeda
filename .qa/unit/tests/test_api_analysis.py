# Categoria: integration
# File sorgente: backend/api/routes/analysis.py

import json
import os
from io import BytesIO

import polars as pl
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(scope="session")
def adult_csv_bytes():
    """Legge le prime 100 righe di adult.csv e le restituisce come bytes."""
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "adult.csv")
    if not os.path.exists(data_path):
        pytest.skip(f"Dataset di test non trovato: {data_path}")
    
    df = pl.read_csv(data_path, n_rows=100, ignore_errors=True)
    buf = BytesIO()
    df.write_csv(buf)
    return buf.getvalue()


def test_upload_csv_file(client, adult_csv_bytes):
    files = {"file": ("adult_subset.csv", BytesIO(adult_csv_bytes), "text/csv")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "file_id" in data
    assert data["n_rows"] == 100
    assert data["n_cols"] == 15
    assert "age" in data["columns"]


def test_upload_parquet_file(client):
    df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    buf = BytesIO()
    df.write_parquet(buf)
    buf.seek(0)
    files = {"file": ("test.parquet", buf, "application/octet-stream")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "file_id" in data
    assert data["n_rows"] == 3


def test_upload_unsupported_format(client):
    files = {"file": ("test.txt", BytesIO(b"hello"), "text/plain")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 400


def test_upload_xlsx_rejected(client):
    """I file XLSX devono essere rifiutati dall'endpoint upload (solo CSV/Parquet)."""
    files = {"file": ("data.xlsx", BytesIO(b"fake excel"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 400


def test_upload_no_extension_rejected(client):
    """File senza estensione devono essere rifiutati."""
    files = {"file": ("noext", BytesIO(b"some content"), "application/octet-stream")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 400


def test_upload_json_rejected(client):
    """I file JSON non sono supportati dall'endpoint upload."""
    files = {"file": ("data.json", BytesIO(b'{"a":1}'), "application/json")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 400


def test_cache_delete_twice(client, adult_csv_bytes):
    """Eliminare due volte lo stesso file: prima 200, seconda 404."""
    files = {"file": ("twice.csv", BytesIO(adult_csv_bytes), "text/csv")}
    upload_resp = client.post("/api/analysis/upload", files=files)
    file_id = upload_resp.json()["file_id"]

    resp1 = client.delete(f"/api/analysis/cache/{file_id}")
    assert resp1.status_code == 200
    assert resp1.json()["deleted"] == file_id

    resp2 = client.delete(f"/api/analysis/cache/{file_id}")
    assert resp2.status_code == 404


def test_analyze_streaming_sse(client, adult_csv_bytes):
    # Upload first
    files = {"file": ("adult_subset.csv", BytesIO(adult_csv_bytes), "text/csv")}
    upload_resp = client.post("/api/analysis/upload", files=files)
    file_id = upload_resp.json()["file_id"]

    # Request SSE
    resp = client.post(
        f"/api/analysis/analyze/{file_id}",
        json={"target": "income", "problem_type": "classification"}
    )
    
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    events_received = set()
    
    # Read the streaming response
    lines = resp.text.splitlines()
    current_event = None
    for line in lines:
        if line:
            text = line if isinstance(line, str) else line.decode("utf-8")
            if text.startswith("event: "):
                current_event = text.split("event: ")[1]
                events_received.add(current_event)
            elif text.startswith("data: ") and current_event:
                data_json = json.loads(text.split("data: ")[1])
                if current_event == "start":
                    assert data_json["n_rows"] == 100
                elif current_event == "meta":
                    assert data_json["target"] == "income"
                elif current_event == "module":
                    assert "module" in data_json
                    assert "data" in data_json
                elif current_event == "done":
                    assert data_json["status"] == "completed"

    # Verify that all key events were emitted
    assert {"start", "meta", "feature_engineering", "module", "done"}.issubset(events_received)


def test_analyze_missing_file_id(client):
    resp = client.post("/api/analysis/analyze/nonexistent-id", json={})
    assert resp.status_code == 404


def test_cache_evict_existing(client, adult_csv_bytes):
    files = {"file": ("evict.csv", BytesIO(adult_csv_bytes), "text/csv")}
    upload_resp = client.post("/api/analysis/upload", files=files)
    file_id = upload_resp.json()["file_id"]

    resp = client.delete(f"/api/analysis/cache/{file_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == file_id

    # verify it's gone
    analyze_resp = client.post(f"/api/analysis/analyze/{file_id}", json={})
    assert analyze_resp.status_code == 404


def test_cache_evict_missing(client):
    resp = client.delete("/api/analysis/cache/not-real-id")
    assert resp.status_code == 404