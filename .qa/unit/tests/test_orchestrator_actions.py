# Categoria: unit
# File sorgente: backend/eda/orchestrator.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-19

import polars as pl

from backend.core.models import CleaningAction
from backend.eda.orchestrator import _apply_single_action, _is_string_like_dtype


def test_is_string_like_dtype():
    assert _is_string_like_dtype(pl.String)
    assert _is_string_like_dtype(pl.Categorical)
    assert _is_string_like_dtype(pl.Enum(["a", "b"]))
    assert not _is_string_like_dtype(pl.Int64)
    assert not _is_string_like_dtype(pl.Float64)


def test_apply_single_action_drop_duplicate_rows():
    df = pl.DataFrame({"a": [1, 2, 2, 3]})
    result = _apply_single_action(df, CleaningAction(type="drop_duplicate_rows"))
    assert len(result) == 3


def test_apply_single_action_exclude_column():
    df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    result = _apply_single_action(df, CleaningAction(type="exclude_column", column="a"))
    assert result.columns == ["b"]


def test_apply_single_action_trim_whitespace():
    df = pl.DataFrame({"name": ["  a  ", "b ", "  c"]})
    result = _apply_single_action(df, CleaningAction(type="trim_whitespace", column="name"))
    assert result["name"].to_list() == ["a", "b", "c"]


def test_apply_single_action_replace_values_exact():
    df = pl.DataFrame({"x": ["A", "B", "A"]})
    result = _apply_single_action(df, CleaningAction(
        type="replace_values",
        column="x",
        params={"match_mode": "exact", "values": ["A"]},
    ))
    assert result["x"].to_list() == [None, "B", None]


def test_apply_single_action_replace_values_case_insensitive():
    df = pl.DataFrame({"x": ["A", "B", "a"]})
    result = _apply_single_action(df, CleaningAction(
        type="replace_values",
        column="x",
        params={"match_mode": "exact_case_insensitive_trimmed", "values": ["a", "A"]},
    ))
    assert result["x"].to_list() == [None, "B", None]


def test_apply_single_action_unknown_returns_unchanged():
    df = pl.DataFrame({"a": [1, 2]})
    result = _apply_single_action(df, CleaningAction(type="unknown", column="a"))
    assert result.equals(df)