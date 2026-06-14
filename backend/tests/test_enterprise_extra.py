# Categoria: unit
# File sorgente: backend/eda/modules/enterprise.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

import pytest
import polars as pl
from eda.modules.enterprise import (
    _detect_pii_candidates,
    _build_profiling,
    _status_from_profile,
    _quality_decomposition,
)


@pytest.fixture
def pii_df():
    return pl.DataFrame({
        "email": ["test@example.com", "admin@test.org", "user@domain.net"],
        "phone": ["+39 02 1234567", "+1 555 0199", "+44 20 7946 0958"],
        "name": ["Mario", "Luigi", "Giovanni"],
        "age": [25, 30, 35],
        "amount": [100.0, 200.0, 300.0],
    })


def test_detect_pii_candidates_finds_email(pii_df):
    result = _detect_pii_candidates(pii_df)
    email_cols = [c for c in result if c["pii_type"] == "email"]
    assert len(email_cols) >= 1
    assert email_cols[0]["column"] == "email"
    assert email_cols[0]["confidence"] >= 80.0


def test_detect_pii_candidates_finds_phone(pii_df):
    result = _detect_pii_candidates(pii_df)
    phone_cols = [c for c in result if c["pii_type"] == "phone"]
    assert len(phone_cols) >= 1
    assert phone_cols[0]["column"] == "phone"


def test_detect_pii_candidates_skips_non_pii(pii_df):
    result = _detect_pii_candidates(pii_df)
    non_pii = [c for c in result if c["column"] in ("age", "amount")]
    assert len(non_pii) == 0


def test_detect_pii_candidates_returns_empty_for_no_pii():
    df = pl.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    result = _detect_pii_candidates(df)
    assert result == []


def test_status_from_profile_returns_critical_for_high_missing():
    status = _status_from_profile({"pct_missing": 50, "semantic_type": "numeric_continuous"})
    assert status == "critical"


def test_status_from_profile_returns_warning_for_medium_missing():
    status = _status_from_profile({"pct_missing": 15, "semantic_type": "numeric_continuous"})
    assert status == "warning"


def test_status_from_profile_returns_ready_for_low_missing():
    status = _status_from_profile({"pct_missing": 2, "semantic_type": "numeric_continuous"})
    assert status == "ready"


def test_status_from_profile_returns_attention_for_id():
    status = _status_from_profile({"pct_missing": 0, "semantic_type": "id"})
    assert status == "attention"


class _FakeDataset:
    file_format = "csv"
    name = "test"

    class _FakePath:
        name = "fake.csv"

        def exists(self):
            return True

        def stat(self):
            class _Stat:
                st_size = 1024

            return _Stat()

    filename = _FakePath()


def test_build_profiling_returns_expected_structure(pii_df):
    base_results = {
        "overview": {
            "columns": [
                {"name": "email", "pct_missing": 0.0},
                {"name": "phone", "pct_missing": 0.0},
                {"name": "name", "pct_missing": 0.0},
                {"name": "age", "pct_missing": 0.0},
                {"name": "amount", "pct_missing": 0.0},
            ]
        }
    }
    semantic_types = {
        "email": "string",
        "phone": "string",
        "name": "string",
        "age": "numeric_discrete",
        "amount": "numeric_continuous",
    }
    groups = {
        "string": ["email", "phone", "name"],
        "numeric_discrete": ["age"],
        "numeric_continuous": ["amount"],
    }
    pii_candidates = _detect_pii_candidates(pii_df)

    result = _build_profiling(pii_df, semantic_types, groups, base_results, _FakeDataset(), _FakeDataset().filename, pii_candidates)
    assert "master_schema" in result
    assert len(result["master_schema"]) == 5
    assert "semantic_summary" in result
