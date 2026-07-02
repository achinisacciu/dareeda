# Categoria: unit
# File sorgente: backend/eda/orchestrator.py

import os
import polars as pl
import pytest

from backend.core.models import AcceptedFeature, CleaningAction
from backend.eda.orchestrator import _compute_accepted_features, _apply_single_action, run_analysis_stateless


@pytest.fixture(scope="session")
def adult_df():
    """Carica un subset di adult.csv per eseguire test end-to-end completi dell'orchestratore."""
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data", "adult.csv"
    )
    if not os.path.exists(data_path):
        pytest.skip(f"Dataset di test non trovato: {data_path}")

    df = pl.read_csv(data_path, n_rows=500, ignore_errors=True)
    return df


@pytest.fixture
def simple_df():
    return pl.DataFrame({
        "a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "b": ["x", "y", "x", "y", "x"],
        "c": [10, 20, 30, 40, 50],
    })


def test_compute_accepted_features_revenue():
    df = pl.DataFrame({"price": [10.0, 20.0], "qty": [2.0, 3.0]})
    accepted = [
        AcceptedFeature(name="total", type="revenue", source_columns=["price", "qty"], formula="ignored", status="accepted")
    ]
    res_df, added, warnings = _compute_accepted_features(df, accepted)
    assert "total" in added
    assert res_df["total"].to_list() == [20.0, 60.0]


def test_compute_accepted_features_margin():
    df = pl.DataFrame({"sell": [100.0, 200.0], "cost": [80.0, 100.0]})
    accepted = [
        AcceptedFeature(name="marg", type="margin", source_columns=["sell", "cost"], formula="ignored", status="accepted")
    ]
    res_df, added, warnings = _compute_accepted_features(df, accepted)
    assert "marg" in added
    assert res_df["marg"].to_list() == [20.0, 100.0]


def test_apply_single_action_trim_whitespace():
    df = pl.DataFrame({"col": [" a ", "b ", " c"]})
    action = CleaningAction(type="trim_whitespace", column="col")
    res = _apply_single_action(df, action)
    assert res["col"].to_list() == ["a", "b", "c"]


def test_apply_single_action_replace_values():
    df = pl.DataFrame({"col": ["yes", "no", "YES", "maybe"]})
    action = CleaningAction(
        type="replace_values", column="col",
        params={"values": ["yes"], "match_mode": "exact_case_insensitive_trimmed"}
    )
    res = _apply_single_action(df, action)
    assert res["col"].to_list() == [None, "no", None, "maybe"]


def test_run_analysis_stateless_adult_dataset(adult_df):
    context = {
        "target": "income",
        "problem_type": "classification",
        "cleaning_actions": [
            {"type": "drop_duplicate_rows"}
        ],
        "accepted_features": [
            {"name": "capital_diff", "type": "margin", "source_columns": ["capital.gain", "capital.loss"], "formula": "ignored", "status": "accepted"}
        ]
    }
    result = run_analysis_stateless(adult_df, "adult.csv", context=context)

    assert result["status"] == "completed"
    assert "meta" in result
    assert result["meta"]["dataset_filename"] == "adult.csv"
    assert result["meta"]["n_rows_full"] <= 500
    assert "feature_engineering" in result
    assert "cleaning" in result["feature_engineering"]
    assert result["feature_engineering"]["cleaning"]["actions"][0].type == "drop_duplicate_rows"
    assert "capital_diff" in result["feature_engineering"]["derived_columns"]
    assert "overview" in result
    assert "n_rows" in result["overview"]
    assert "n_cols" in result["overview"]
    assert "data_quality" in result
    assert "duplicates" in result["data_quality"]
    assert "univariate" in result
    assert "age" in result["univariate"]
    assert "income" in result["univariate"]
    assert "bivariate" in result
    assert "insights" in result
    assert "generated" in result["insights"]


def test_compute_accepted_features_missing_sources_are_skipped(simple_df):
    accepted = [
        AcceptedFeature(name="bad", type="derived_feature", source_columns=["nonexistent"], formula="x", status="accepted"),
    ]
    result_df, added, warnings = _compute_accepted_features(simple_df, accepted)
    assert "bad" not in result_df.columns
    assert added == []


def test_compute_accepted_features_empty_list_returns_unchanged(simple_df):
    result_df, added, warnings = _compute_accepted_features(simple_df, [])
    assert result_df.columns == simple_df.columns
    assert added == []
    assert warnings == []


def test_compute_accepted_features_requires_name_and_formula():
    df = pl.DataFrame({"x": [1, 2, 3]})

    result_df, added, warnings = _compute_accepted_features(
        df, [AcceptedFeature(name="", type="", source_columns=["x"], formula="x + 1")]
    )
    assert added == []

    result_df, added, warnings = _compute_accepted_features(
        df, [AcceptedFeature(name="y", type="", source_columns=["x"], formula="")]
    )
    assert added == []


def test_compute_accepted_features_all_types(simple_df):
    df = pl.DataFrame({
        "price": [100.0, 200.0],
        "cost": [80.0, 100.0],
        "discount": [0.1, 0.2],
        "date_str": ["2023-01-01", "2024-12-31"]
    })
    accepted = [
        AcceptedFeature(name="margin_pct", type="margin_pct", source_columns=["price", "cost"], formula="ignored", status="accepted"),
        AcceptedFeature(name="ratio", type="ratio", source_columns=["price", "cost"], formula="ignored", status="accepted"),
        AcceptedFeature(name="discount_val", type="discount", source_columns=["price", "discount"], formula="ignored", status="accepted"),
        AcceptedFeature(name="discount_val2", type="discount", source_columns=["price", "cost"], formula="ignored", status="accepted"),
        AcceptedFeature(name="year_col", type="derived_feature", source_columns=["date_str"], formula="year(date_str)", status="accepted"),
        AcceptedFeature(name="month_col", type="derived_feature", source_columns=["date_str"], formula="month(date_str)", status="accepted"),
        AcceptedFeature(name="bad_feat", type="margin", source_columns=["price", "missing_col"], formula="ignored", status="accepted"),
    ]
    res_df, added, warnings = _compute_accepted_features(df, accepted)

    assert "margin_pct" in added
    assert "ratio" in added
    assert "discount_val" in added
    assert "discount_val2" in added
    assert "year_col" in added
    assert "month_col" in added
    assert "bad_feat" not in added

    assert res_df["margin_pct"].to_list() == [20.0, 50.0]
    assert res_df["ratio"].to_list() == [1.25, 2.0]
    assert res_df["discount_val"].to_list() == [90.0, 160.0]
    assert res_df["year_col"].to_list() == [2023, 2024]
    assert res_df["month_col"].to_list() == [1, 12]