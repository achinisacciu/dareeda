# Categoria: unit
# File sorgente: backend/eda/modules/timeseries.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

from datetime import datetime

import polars as pl
import pytest
from eda.modules.timeseries import _analyze_series, run


@pytest.fixture
def ts_df():
    return pl.DataFrame({
        "date": pl.datetime_range(
            datetime(2024, 1, 1), datetime(2024, 2, 19), interval="1d", eager=True
        ),
        "value": [10 + i * 0.5 for i in range(50)],
    })


def test_run_returns_inactive_when_no_datetime():
    df = pl.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    result = run(df, df, {}, {"numeric_continuous": ["x", "y"]})
    assert result["active"] is False
    assert "reason" in result


def test_run_returns_inactive_when_no_numeric():
    df = pl.DataFrame({
        "date": pl.datetime_range(datetime(2024, 1, 1), datetime(2024, 1, 2), interval="1d", eager=True),
        "text": ["a", "b"],
    })
    result = run(df, df, {"datetime": ["date"]}, {"text": ["text"]})
    assert result["active"] is False


def test_run_returns_active_with_valid_data(ts_df):
    groups = {
        "datetime": ["date"],
        "numeric_continuous": ["value"],
    }
    semantic_types = {"date": "datetime", "value": "numeric_continuous"}
    result = run(ts_df, ts_df, semantic_types, groups)
    assert result["active"] is True
    assert "ts_column" in result
    assert "analyses" in result


def test_analyze_series_returns_expected_keys(ts_df):
    result = _analyze_series(ts_df, "date", "value")
    assert "metadata" in result
    assert "charts" in result
    assert "line" in result["charts"]
    assert "stationarity" in result


def test_analyze_series_returns_error_for_short_series():
    df = pl.DataFrame({
        "d": pl.datetime_range(datetime(2024, 1, 1), datetime(2024, 1, 2), interval="1d", eager=True),
        "v": [1, 2],
    })
    result = _analyze_series(df, "d", "v")
    assert "error" in result
