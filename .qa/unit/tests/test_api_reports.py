# Categoria: integration
# File sorgente: backend/api/routes/reports.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_generate_pdf_returns_200_with_valid_payload():
    payload = {"analysis_data": {"modules": {}, "meta": {}}}
    with patch("api.routes.reports.generate_report_in_memory") as mock_gen:
        mock_buf = MagicMock()
        mock_buf.getvalue.return_value = b"%PDF-1.4 fake"
        mock_gen.return_value = mock_buf

        resp = client.post("/api/reports/generate-pdf", json=payload)

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"
