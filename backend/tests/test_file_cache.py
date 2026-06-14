# Categoria: unit
# File sorgente: backend/core/file_cache.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

import pytest
import polars as pl
from datetime import datetime, timedelta
from core.file_cache import store, get, delete, _evict_expired


@pytest.fixture
def sample_df():
    return pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


def test_store_returns_file_id(sample_df):
    fid = store(sample_df, "test.csv")
    assert isinstance(fid, str)
    assert len(fid) > 0
    delete(fid)


def test_get_returns_entry_after_store(sample_df):
    fid = store(sample_df, "data.parquet")
    entry = get(fid)
    assert entry is not None
    assert entry["filename"] == "data.parquet"
    assert entry["df"].height == 3
    delete(fid)


def test_get_returns_none_for_missing_id():
    assert get("00000000-0000-0000-0000-000000000000") is None


def test_delete_removes_entry(sample_df):
    fid = store(sample_df, "del.csv")
    assert get(fid) is not None
    delete(fid)
    assert get(fid) is None


def test_evict_expired_removes_old_entries(sample_df):
    fid = store(sample_df, "old.csv")
    entry = get(fid)
    assert entry is not None
    entry["uploaded_at"] = datetime.utcnow() - timedelta(minutes=31)
    from core.file_cache import _CACHE
    _CACHE[fid] = entry
    _evict_expired()
    assert get(fid) is None
