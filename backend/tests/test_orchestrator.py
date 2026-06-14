# Categoria: unit
# File sorgente: backend/eda/orchestrator.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

import pytest
import polars as pl
from backend.eda.orchestrator import _compute_accepted_features


@pytest.fixture
def simple_df():
    return pl.DataFrame({
        "a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "b": ["x", "y", "x", "y", "x"],
        "c": [10, 20, 30, 40, 50],
    })


def test_compute_accepted_features_missing_sources_are_skipped(simple_df):
    accepted = [
        {
            "name": "bad",
            "type": "derived_feature",
            "source_columns": ["nonexistent"],
            "formula": "x",
            "status": "accepted",
        }
    ]
    result_df, added = _compute_accepted_features(simple_df, accepted)
    assert "bad" not in result_df.columns
    assert added == []


def test_compute_accepted_features_empty_list_returns_unchanged(simple_df):
    result_df, added = _compute_accepted_features(simple_df, [])
    assert result_df.columns == simple_df.columns
    assert added == []


def test_compute_accepted_features_derived_year(simple_df):
    accepted = [
        {
            "name": "year",
            "type": "derived_feature",
            "source_columns": ["b"],
            "formula": "year(b)",
            "status": "accepted",
        }
    ]
    result_df, added = _compute_accepted_features(simple_df, accepted)
    assert "year" not in result_df.columns or added == []


def test_compute_accepted_features_requires_name_and_formula():
    df = pl.DataFrame({"x": [1, 2, 3]})

    result_df, added = _compute_accepted_features(df, [{"source_columns": ["x"], "formula": "x + 1"}])
    assert added == []

    result_df, added = _compute_accepted_features(df, [{"name": "y", "source_columns": ["x"]}])
    assert added == []
