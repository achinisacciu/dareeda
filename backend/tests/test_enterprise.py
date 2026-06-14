# Categoria: unit
# File sorgente: backend/eda/modules/enterprise.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

import pytest
from unittest.mock import patch, MagicMock
import polars as pl
from eda.modules.enterprise import (
    _safe_git_commit,
    _sha256_file,
    _series_unique_ratio,
    _quality_decomposition,
)


@pytest.fixture
def simple_df():
    return pl.DataFrame({
        "id": [1, 2, 3, 4],
        "value": [10.0, 20.0, 30.0, 40.0],
        "cat": ["a", "b", "a", "b"],
    })


def test_safe_git_commit_returns_none_on_failure(tmp_path):
    result = _safe_git_commit(tmp_path)
    assert result is None


def test_sha256_file_returns_none_for_missing():
    from pathlib import Path
    result = _sha256_file(Path("/nonexistent/path/file.csv"))
    assert result is None


def test_series_unique_ratio_basic():
    s = pl.Series("x", [1, 1, 2, 2, 3])
    ratio = _series_unique_ratio(s, n_rows=5)
    assert ratio == 60.0


def test_series_unique_ratio_zero_rows():
    s = pl.Series("x", [1, 2, 3])
    ratio = _series_unique_ratio(s, n_rows=0)
    assert ratio == 0.0


def test_quality_decomposition_returns_dict(simple_df):
    groups = {"numeric_continuous": ["value"], "categorical_nominal": ["cat"]}
    base = {
        "data_quality": {
            "completeness": 95.0,
            "uniqueness": 80.0,
            "validity": 90.0,
            "consistency": 85.0,
            "accuracy": 88.0,
            "timeliness": 92.0,
            "inconsistencies": {},
            "pii_candidates": [],
            "pct_missing": 2.0,
            "pct_duplicate_rows": 1.0,
        }
    }
    result = _quality_decomposition(simple_df, groups, base)
    assert "dimensions" in result
    assert "total_score" in result
    assert isinstance(result["total_score"], float)
