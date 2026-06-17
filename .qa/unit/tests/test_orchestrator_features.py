# Categoria: unit
# File sorgente: backend/eda/orchestrator.py
# Creato: 2026-06-14

import polars as pl
import pytest

from backend.eda.orchestrator import _compute_accepted_features


@pytest.fixture
def df():
    return pl.DataFrame({
        "price": [100.0, 200.0, 300.0],
        "cost": [60.0, 120.0, 180.0],
        "qty": [2.0, 3.0, 4.0],
        "discount": [10.0, 20.0, 30.0],
        "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
    })


def test_compute_accepted_features_revenue(df):
    result_df, added = _compute_accepted_features(df, [
        {"name": "rev", "type": "revenue", "source_columns": ["price", "qty"], "formula": "x", "status": "accepted"}
    ])
    assert "rev" in result_df.columns
    assert added == ["rev"]
    assert result_df["rev"].to_list() == [200.0, 600.0, 1200.0]


def test_compute_accepted_features_margin(df):
    result_df, added = _compute_accepted_features(df, [
        {"name": "marg", "type": "margin", "source_columns": ["price", "cost"], "formula": "x", "status": "accepted"}
    ])
    assert "marg" in result_df.columns
    assert added == ["marg"]
    assert result_df["marg"].to_list() == [40.0, 80.0, 120.0]


def test_compute_accepted_features_ratio(df):
    result_df, added = _compute_accepted_features(df, [
        {"name": "ratio", "type": "ratio", "source_columns": ["price", "qty"], "formula": "x", "status": "accepted"}
    ])
    assert "ratio" in result_df.columns
    assert added == ["ratio"]
    assert result_df["ratio"].to_list() == [50.0, 200.0 / 3.0, 75.0]


def test_compute_accepted_features_discount_percent(df):
    result_df, added = _compute_accepted_features(df, [
        {"name": "net", "type": "discount", "source_columns": ["price", "discount"],
         "formula": "x", "status": "accepted"}
    ])
    assert "net" in result_df.columns
    assert added == ["net"]
    assert result_df["net"].to_list() == [90.0, 160.0, 210.0]


def test_compute_accepted_features_discount_decimal(df):
    df2 = df.with_columns(pl.lit(0.1).alias("disc_dec"))
    result_df, added = _compute_accepted_features(df2, [
        {"name": "net", "type": "discount", "source_columns": ["price", "disc_dec"],
         "formula": "x", "status": "accepted"}
    ])
    assert "net" in result_df.columns
    assert added == ["net"]
    assert result_df["net"].to_list() == [90.0, 180.0, 270.0]
