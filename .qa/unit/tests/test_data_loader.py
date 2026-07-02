# Categoria: unit
# File sorgente: backend/core/data_loader.py

import os
from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest

from core.data_loader import (
    get_memory_mb,
    get_preview,
    load_file,
)
from polars.exceptions import PolarsError


@pytest.fixture(scope="session")
def adult_csv_path():
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "adult.csv")
    if not os.path.exists(data_path):
        pytest.skip(f"Dataset di test non trovato: {data_path}")
    return data_path


def test_load_real_adult_csv(adult_csv_path):
    df = load_file(adult_csv_path)
    
    assert isinstance(df, pl.DataFrame)
    assert df.height > 1000
    assert df.width == 15
    assert "age" in df.columns
    assert "income" in df.columns


def test_load_csv(tmp_path):
    f = tmp_path / "test.csv"
    f.write_text(
        "a,b,c\n1,2,3\n4,5,6\n",
        encoding="utf-8",
    )

    df = load_file(f)

    assert isinstance(df, pl.DataFrame)
    assert df.shape == (2, 3)
    assert df.columns == ["a", "b", "c"]


def test_load_json(tmp_path):
    f = tmp_path / "test.json"

    f.write_text(
        '[{"a":1,"b":2},{"a":3,"b":4}]',
        encoding="utf-8",
    )

    df = load_file(f)

    assert isinstance(df, pl.DataFrame)
    assert df.shape == (2, 2)


def test_unsupported_format(tmp_path):
    f = tmp_path / "test.parquet"
    f.write_bytes(b"fake")

    with pytest.raises(ValueError) as exc:
        load_file(f)

    assert "Formato non supportato" in str(exc.value)
    assert ".parquet" in str(exc.value)


def test_load_excel_mock():
    fake_df = pl.DataFrame({"a": [1]})
    with patch("core.data_loader.pl.read_excel") as mock_read:
        mock_read.return_value = fake_df
        loaded = load_file("fake.xlsx")
        assert loaded.equals(fake_df)


def test_csv_fallback_semicolon_reader():
    fake_df = pl.DataFrame({"a": [1]})

    with patch("core.data_loader.pl.read_csv") as mock_read:
        mock_read.side_effect = [
            PolarsError("csv failed"),
            fake_df,
        ]

        result = load_file("fake.csv")

    assert result.equals(fake_df)
    assert mock_read.call_count == 2


def test_json_fallback_ndjson():
    fake_df = pl.DataFrame({"a": [1]})

    with patch("core.data_loader.pl.read_json") as mock_json:
        with patch("core.data_loader.pl.read_ndjson") as mock_ndjson:
            mock_json.side_effect = PolarsError("json failed")
            mock_ndjson.return_value = fake_df

            result = load_file("fake.json")

    assert result.equals(fake_df)
    mock_json.assert_called_once()
    mock_ndjson.assert_called_once()


def test_missing_file_raises_exception():
    with pytest.raises(Exception):
        load_file("file_that_does_not_exist.csv")


def test_memory_mb_returns_float(adult_csv_path):
    df = load_file(adult_csv_path)
    result = get_memory_mb(df)

    assert isinstance(result, float)
    assert result > 0.0


def test_preview_returns_requested_rows(adult_csv_path):
    df = load_file(adult_csv_path)
    preview = get_preview(df, n=10)

    assert len(preview) == 10
    assert "age" in preview[0]


def test_preview_with_zero_rows():
    df = pl.DataFrame({"a": [1, 2, 3]})
    preview = get_preview(df, n=0)
    assert preview == []


def test_preview_with_more_rows_than_available():
    df = pl.DataFrame({"a": [1, 2, 3]})
    preview = get_preview(df, n=100)
    assert len(preview) == 3
