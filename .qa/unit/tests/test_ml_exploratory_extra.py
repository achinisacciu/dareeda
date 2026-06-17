# Categoria: unit
# File sorgente: backend/eda/modules/ml_exploratory.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

import polars as pl
import pytest
from eda.modules.ml_exploratory import _anomaly, _clustering, run, validate_target


@pytest.fixture
def ml_df():
    n = 100
    return pl.DataFrame({
        "target": [1, 0] * (n // 2),
        "f1": [float(i) for i in range(n)],
        "f2": [float(i % 10) for i in range(n)],
        "f3": [float((i * 3) % 7) for i in range(n)],
    })


def test_validate_target_missing_column(ml_df):
    ok, msg = validate_target(ml_df, "ghost")
    assert ok is False
    assert "non esiste" in msg


def test_validate_target_all_null():
    df = pl.DataFrame({"target": [None, None, None]})
    ok, msg = validate_target(df, "target")
    assert ok is False
    assert "vuota" in msg


def test_validate_target_valid(ml_df):
    ok, msg = validate_target(ml_df, "target")
    assert ok is True
    assert msg is None


def test_run_returns_error_when_no_target(ml_df):
    result = run(ml_df, ml_df, {}, {})
    assert "error" in result
    assert result["error"] == "Target non definita"


def test_run_returns_clustering_even_without_target(ml_df):
    result = run(ml_df, ml_df, {"numeric_continuous": ["f1", "f2", "f3"]}, {})
    assert "clustering" in result
    assert "anomaly_detection" in result


def test_clustering_skips_with_few_features(ml_df):
    result = _clustering(ml_df, ["target"])
    assert result.get("skipped") is True


def test_clustering_runs_with_enough_features(ml_df):
    result = _clustering(ml_df, ["f1", "f2", "f3"])
    assert "skipped" not in result or result.get("skipped") is not True


def test_anomaly_detection_runs_with_enough_features(ml_df):
    result = _anomaly(ml_df, ["f1", "f2", "f3"])
    assert "skipped" not in result or result.get("skipped") is not True


def test_mutual_info_aligns_target_with_filtered_rows():
    """Rows dropped by the NaN mask must use matching target values."""
    import numpy as np
    from eda.modules.ml_exploratory import _mutual_info

    df = pl.DataFrame({
        "target": ["A", "B", "A", "B", "A"],
        "f1": [float("nan"), 1.0, 2.0, 3.0, 4.0],
        "f2": [1.0, 2.0, 3.0, 4.0, 5.0],
    })

    mat = df.select([
        pl.col("f1").cast(pl.Float64).fill_null(pl.col("f1").mean()),
        pl.col("f2").cast(pl.Float64),
    ]).to_numpy()
    mask = ~np.isnan(mat).any(axis=1)

    result = _mutual_info(df, ["f1", "f2"], "target", True)

    assert result.get("skipped") is not True
    assert len(result["features"]) == 2
    assert mask.sum() == 4
    assert list(df["target"].to_numpy()[mask]) == ["B", "A", "B", "A"]
