from pathlib import Path

import polars as pl
import pytest
from core.data_loader import get_memory_mb, get_preview, load_file


def make_csv(path, content):
    Path(path).write_text(content, encoding="utf-8")

def test_load_csv(tmp_path):
    f = tmp_path / "test.csv"
    f.write_text("a,b,c\n1,2,3\n4,5,6\n", encoding="utf-8")
    df = load_file(f)
    assert isinstance(df, pl.DataFrame)
    assert df.shape == (2, 3)

def test_load_json(tmp_path):
    f = tmp_path / "test.json"
    f.write_text('[{"a":1,"b":2},{"a":3,"b":4}]', encoding="utf-8")
    df = load_file(f)
    assert df.shape == (2, 2)

def test_unsupported_format(tmp_path):
    f = tmp_path / "test.parquet"
    f.write_bytes(b"fake")
    with pytest.raises(ValueError, match="Formato non supportato"):
        load_file(f)

def test_memory_mb():
    df = pl.DataFrame({"x": list(range(1000))})
    mb = get_memory_mb(df)
    assert mb >= 0

def test_preview():
    df = pl.DataFrame({"a": list(range(50))})
    preview = get_preview(df, n=10)
    assert len(preview) == 10
    assert "a" in preview[0]
