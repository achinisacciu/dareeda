# Categoria: unit
# File sorgente: backend/eda/orchestrator.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

import polars as pl
import pytest

from backend.eda.orchestrator import _compute_accepted_features, run_analysis_stateless


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


def test_run_analysis_stateless_returns_completed_status(simple_df):
    result = run_analysis_stateless(simple_df, "test.csv")
    assert result["status"] == "completed"
    assert "meta" in result
    assert result["meta"]["dataset_filename"] == "test.csv"


def test_run_analysis_stateless_with_accepted_features():
    df = pl.DataFrame({
        "price": [100.0, 200.0, 300.0],
        "qty": [1.0, 2.0, 3.0],
    })
    result = run_analysis_stateless(
        df, "test.csv",
        context={"accepted_features": [{"name": "total", "type": "revenue", "source_columns": ["price", "qty"], "formula": "x"}]}
    )
    assert result["status"] == "completed"
    assert "feature_engineering" in result


def test_run_analysis_stateless_with_cleaning_actions():
    df = pl.DataFrame({
        "a": [1.0, 2.0, 3.0],
        "b": ["x", "y", "z"],
    })
    result = run_analysis_stateless(
        df, "test.csv",
        context={"cleaning_actions": [{"type": "exclude_column", "column": "b"}]}
    )
    assert result["status"] == "completed"
    assert "feature_engineering" in result
    assert "cleaning" in result["feature_engineering"]


def test_run_analysis_stateless_with_context_target():
    df = pl.DataFrame({
        "num": [1.0, 2.0, 3.0],
        "cat": ["a", "b", "c"],
    })
    result = run_analysis_stateless(
        df, "test.csv",
        context={"target": "num", "problem_type": "regression"}
    )
    assert result["status"] == "completed"
    assert result["meta"]["target"] == "num"
