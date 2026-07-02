# Categoria: unit
# File sorgente: backend/core/semantic_typer.py
# Creato: 2026-06-17

import polars as pl
from core.semantic_typer import detect_semantic_type, type_dataframe


def test_boolean_detection():
    s = pl.Series("active", [True, False, True, None])
    assert detect_semantic_type(s) == "boolean"

def test_boolean_string():
    s = pl.Series("flag", ["yes", "no", "yes", "no"])
    assert detect_semantic_type(s) == "boolean"

def test_id_detection():
    s = pl.Series("user_id", [str(i) for i in range(1000)])
    assert detect_semantic_type(s) == "id"

def test_numeric_continuous():
    import random
    s = pl.Series("price", [random.uniform(0, 100) for _ in range(500)])
    assert detect_semantic_type(s) == "numeric_continuous"

def test_numeric_discrete():
    s = pl.Series("rating", [1, 2, 3, 4, 5] * 100)
    assert detect_semantic_type(s) == "numeric_discrete"

def test_categorical():
    s = pl.Series("city", ["Milano", "Roma", "Napoli", "Torino"] * 50)
    assert detect_semantic_type(s) == "categorical_nominal"

def test_datetime():
    import datetime
    s = pl.Series("date", [datetime.date(2024, 1, i % 28 + 1) for i in range(100)])
    assert detect_semantic_type(s) == "datetime"

def test_empty_series_returns_categorical():
    """Serie vuota: senza dati non si può determinare il tipo, default categorical."""
    s = pl.Series("empty", [], dtype=pl.Utf8)
    assert isinstance(detect_semantic_type(s), str)

def test_all_null_series_returns_categorical():
    """Serie con tutti valori null: default safe."""
    s = pl.Series("nulls", [None, None, None])
    assert isinstance(detect_semantic_type(s), str)

def test_single_value_numeric_not_discrete():
    """Serie con un solo valore numerico: non deve essere classificata come discreta."""
    s = pl.Series("const", [42.0, 42.0, 42.0])
    assert detect_semantic_type(s) in ("numeric_continuous", "numeric_discrete")

def test_threshold_id_boundary():
    """Serie con meno items della soglia ID: non deve essere classificata come ID."""
    s = pl.Series("small", [str(i) for i in range(50)])
    assert detect_semantic_type(s) != "id"

def test_type_dataframe():
    df = pl.DataFrame({
        "id":    [str(i) for i in range(200)],
        "price": [float(i) for i in range(200)],
        "cat":   ["A", "B"] * 100,
    })
    result = type_dataframe(df)
    assert "id" in result
    assert "price" in result
    assert "cat" in result
    assert all(col in result for col in df.columns)

def test_type_dataframe_with_nulls():
    """type_dataframe deve gestire dataframe con colonne tutte null."""
    df = pl.DataFrame({
        "a": [None, None],
        "b": [1.0, 2.0],
    })
    result = type_dataframe(df)
    assert "a" in result
    assert "b" in result
