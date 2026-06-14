# Categoria: unit
# File sorgente: backend/eda/modules/bivariate.py (complementare)
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

import pytest
import polars as pl
from eda.modules.bivariate import run


@pytest.fixture
def bivar_df():
    return pl.DataFrame({
        "num1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "num2": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0],
        "cat": ["a", "b", "a", "b", "a", "b", "a", "b"],
    })


def test_run_returns_active_with_numeric_columns(bivar_df):
    groups = {
        "numeric_continuous": ["num1", "num2"],
        "categorical_nominal": ["cat"],
    }
    result = run(bivar_df, bivar_df, {}, groups)
    assert "num_num" in result or "active" in result


def test_run_handles_empty_dataframe():
    df = pl.DataFrame({"num1": [], "num2": []})
    groups = {"numeric_continuous": ["num1", "num2"]}
    result = run(df, df, {}, groups)
    assert "num_num" in result or "active" in result
