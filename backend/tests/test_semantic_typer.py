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
