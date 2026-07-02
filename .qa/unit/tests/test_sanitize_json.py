# Categoria: unit
# File sorgente: backend/api/routes/analysis.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-17

import math

import numpy as np
import pytest

from backend.api.routes.analysis import _sanitize_for_json


@pytest.mark.parametrize("value,expected", [
    (True, True),
    (np.bool_(True), True),
    (1.5, 1.5),
    (np.float64(1.5), 1.5),
    (42, 42),
    (np.int64(42), 42),
    ("hello", "hello"),
    (None, None),
    (math.nan, None),
    (np.nan, None),
    (float("inf"), None),
    (float("-inf"), None),
    (np.inf, None),
    (np.float32(3.14), 3.140000104904175),
])
def test_sanitize_for_json_primitives(value, expected):
    assert _sanitize_for_json(value) == expected


def test_sanitize_for_json_nested_dict():
    data = {"a": np.int64(1), "b": {"c": np.float64(2.5)}}
    result = _sanitize_for_json(data)
    assert result == {"a": 1, "b": {"c": 2.5}}


def test_sanitize_for_json_deeply_nested():
    data = {"level1": {"level2": {"level3": np.int64(42), "nan": np.nan}}}
    result = _sanitize_for_json(data)
    assert result == {"level1": {"level2": {"level3": 42, "nan": None}}}


def test_sanitize_for_json_mixed_list():
    data = [np.int64(1), {"key": np.float64(2.5), "nested_list": [np.nan, np.inf]}, "end"]
    result = _sanitize_for_json(data)
    assert result[0] == 1
    assert isinstance(result[1], dict)
    assert result[1]["key"] == 2.5
    assert result[1]["nested_list"] == [None, None]
    assert result[2] == "end"


def test_sanitize_for_json_list_with_numpy():
    data = [np.int64(1), np.float64(2.5), np.nan]
    result = _sanitize_for_json(data)
    assert result == [1, 2.5, None]


def test_sanitize_for_json_empty_structures():
    assert _sanitize_for_json({}) == {}
    assert _sanitize_for_json([]) == []
    assert _sanitize_for_json(np.array([])) is not None
