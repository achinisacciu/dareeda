# Categoria: integration
# File sorgente: backend/api/routes/reports.py

import json
from io import BytesIO

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_generate_pdf_returns_pdf_response():
    """Testa la generazione del PDF con un payload simulato verosimile, senza mock."""
    payload = {
        "analysis_data": {
            "meta": {
                "dataset_filename": "adult.csv",
                "generated_at": "2026-06-17T12:00:00Z",
                "target": "income",
                "problem_type": "classification",
                "n_rows_full": 500,
                "n_cols": 15,
                "sampled": False
            },
            "overview": {
                "n_rows": 500,
                "n_cols": 15,
                "duplicate_rows": 0,
                "total_missing_pct": 0.0
            },
            "data_quality": {
                "missing_values": {}
            },
            "feature_engineering": {
                "derived_columns": [],
                "cleaning": {"actions": [], "rows_removed": 0, "cols_removed": 0}
            },
            "univariate": {
                "variables": {
                    "age": {
                        "type": "numeric",
                        "missing_count": 0,
                        "min": 17,
                        "max": 90,
                        "mean": 38.5,
                        "std": 13.6
                    }
                }
            },
            "insights": {
                "business_insights": ["Insight finto per test"]
            }
        }
    }

    resp = client.post("/api/reports/generate-pdf", json=payload)

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "content-disposition" in resp.headers
    assert "dareeda_report.pdf" in resp.headers["content-disposition"]
    assert resp.content.startswith(b"%PDF-")


def test_generate_pdf_rejects_missing_analysis_data():
    resp = client.post("/api/reports/generate-pdf", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body
    assert len(body["detail"]) > 0


def test_generate_pdf_rejects_string_analysis_data():
    resp = client.post("/api/reports/generate-pdf", json={"analysis_data": "not-a-dict"})
    assert resp.status_code == 422


def test_generate_pdf_rejects_null_analysis_data():
    resp = client.post("/api/reports/generate-pdf", json={"analysis_data": None})
    assert resp.status_code == 422
