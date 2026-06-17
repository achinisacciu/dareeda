# Categoria: unit
# File sorgente: backend/eda/modules/enterprise.py
# Creato: 2026-06-14


import polars as pl
import pytest

from backend.eda.modules.enterprise import _build_profiling


class _FakeDataset:
    filename = "test.csv"
    file_format = "csv"


class _FakePath:
    def __init__(self):
        self.name = "test.csv"

    def exists(self):
        return True

    def stat(self):
        class _Stat:
            st_size = 1024

        return _Stat()


def test_build_profiling_contains_expected_keys():
    df = pl.DataFrame({
        "id": [1, 2, 3],
        "value": [10.0, 20.0, 30.0],
        "cat": ["a", "b", "a"],
    })
    semantic_types = {
        "id": "id",
        "value": "numeric_continuous",
        "cat": "categorical_nominal",
    }
    groups = {
        "id": ["id"],
        "numeric_continuous": ["value"],
        "categorical_nominal": ["cat"],
    }
    base_results = {}
    pii_candidates = []
    result = _build_profiling(df, semantic_types, groups, base_results, _FakeDataset(), _FakePath(), pii_candidates)
    assert "master_schema" in result
    assert len(result["master_schema"]) == 3
    assert "semantic_summary" in result
    cols = {item["column"]: item for item in result["master_schema"]}
    assert cols["value"]["uniqueness_ratio"] == 100.0
    assert cols["cat"]["uniqueness_ratio"] == pytest.approx(66.67, abs=0.1)
