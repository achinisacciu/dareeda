# Categoria: unit
# File sorgente: backend/api/routes/analysis.py
# Creato: 2026-06-17

from io import BytesIO
import polars as pl
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_upload_csv_file():
    csv_content = b"col1,col2,col3\n1,2,3\n4,5,6\n"
    files = {"file": ("test.csv", BytesIO(csv_content), "text/csv")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "file_id" in data
    assert data["n_rows"] == 2
    assert data["n_cols"] == 3


def test_upload_parquet_file():
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


def test_upload_unsupported_format():
    files = {"file": ("test.txt", BytesIO(b"hello"), "text/plain")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 400


def test_upload_file_too_large():
    large_content = b"a" * (101 * 1024 * 1024)
    files = {"file": ("large.csv", BytesIO(large_content), "text/csv")}
    resp = client.post("/api/analysis/upload", files=files)
    assert resp.status_code == 413


def test_analyze_missing_file_id():
    resp = client.post("/api/analysis/analyze/nonexistent-id", json={})
    assert resp.status_code == 404


def test_analyze_with_accepted_features_string():
    csv_content = b"col1,col2\n1,2\n3,4\n"
    files = {"file": ("test.csv", BytesIO(csv_content), "text/csv")}
    upload_resp = client.post("/api/analysis/upload", files=files)
    file_id = upload_resp.json()["file_id"]

    resp = client.post(
        f"/api/analysis/analyze/{file_id}",
        json={"accepted_features": ["new_col"]},
    )
    assert resp.status_code == 200


def test_cache_evict_existing():
    csv_content = b"x,y\n1,2\n"
    files = {"file": ("evict.csv", BytesIO(csv_content), "text/csv")}
    upload_resp = client.post("/api/analysis/upload", files=files)
    file_id = upload_resp.json()["file_id"]

    resp = client.delete(f"/api/analysis/cache/{file_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == file_id


def test_cache_evict_missing():
    resp = client.delete("/api/analysis/cache/not-real-id")
    assert resp.status_code == 404