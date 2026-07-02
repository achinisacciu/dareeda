# Categoria: unit
# File sorgente: backend/core/file_cache.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-17

from datetime import UTC, datetime, timedelta

import polars as pl
import pytest
from core.file_cache import _CACHE, _evict_expired, delete, get, store


@pytest.fixture(autouse=True)
def clear_cache():
    """Pulisce la cache prima e dopo ogni test per isolamento totale."""
    _CACHE.clear()
    yield
    _CACHE.clear()


@pytest.fixture
def sample_df():
    return pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


def test_store_returns_file_id(sample_df):
    fid = store(sample_df, "test.csv")
    assert isinstance(fid, str)
    assert len(fid) > 0
    assert len(fid) == 36  # UUID4 standard length con trattini
    # Verifica che sia un UUID valido
    import uuid
    assert uuid.UUID(fid, version=4)


def test_get_returns_entry_after_store(sample_df):
    fid = store(sample_df, "data.parquet")
    entry = get(fid)
    assert entry is not None
    assert entry["filename"] == "data.parquet"
    assert entry["df"].height == 3
    assert "uploaded_at" in entry


def test_get_returns_none_for_missing_id():
    assert get("00000000-0000-0000-0000-000000000000") is None


def test_get_returns_none_for_empty_string_id():
    assert get("") is None


def test_delete_removes_entry(sample_df):
    fid = store(sample_df, "del.csv")
    assert get(fid) is not None
    delete(fid)
    assert get(fid) is None


def test_delete_non_existent_returns_none():
    assert delete("00000000-0000-0000-0000-000000000000") is None


def test_evict_expired_removes_old_entries(sample_df):
    fid = store(sample_df, "old.csv")
    entry = get(fid)
    assert entry is not None
    entry["uploaded_at"] = datetime.now(UTC) - timedelta(minutes=31)
    _CACHE[fid] = entry
    _evict_expired()
    assert get(fid) is None


def test_store_preserves_filename_whitespace(sample_df):
    """Il filename viene salvato così com'è (spazi finali non vengono tagliati)."""
    fid = store(sample_df, "  spaced name.csv  ")
    entry = get(fid)
    assert entry is not None
    assert entry["filename"] == "  spaced name.csv  "
    delete(fid)
