"""
core/file_cache.py

Cache in-memory per i DataFrame caricati via upload.
Mappa file_id -> { "df": pl.DataFrame, "filename": str, "uploaded_at": datetime }

In produzione sostituire con Redis + serializzazione Arrow/Parquet.
"""

import uuid
from datetime import UTC, datetime, timedelta

import polars as pl

# Dizionario principale: { file_id: { df, filename, uploaded_at } }
_CACHE: dict[str, dict] = {}

# TTL: i file vengono rimossi dopo 30 minuti di inattività
_TTL_MINUTES = 30


def store(df: pl.DataFrame, filename: str) -> str:
    """Salva un DataFrame nella cache e restituisce il file_id generato."""
    _evict_expired()
    file_id = str(uuid.uuid4())
    _CACHE[file_id] = {
        "df": df,
        "filename": filename,
        "uploaded_at": datetime.now(UTC),
    }
    return file_id


def get(file_id: str) -> dict | None:
    """
    Recupera la entry dalla cache.
    Restituisce None se non esiste o se è scaduta.
    """
    _evict_expired()
    return _CACHE.get(file_id)


def delete(file_id: str) -> None:
    """Rimuove esplicitamente un file dalla cache."""
    _CACHE.pop(file_id, None)


def _evict_expired() -> None:
    """Rimuove le entry più vecchie del TTL."""
    cutoff = datetime.now(UTC) - timedelta(minutes=_TTL_MINUTES)
    expired = [fid for fid, entry in _CACHE.items() if entry["uploaded_at"] < cutoff]
    for fid in expired:
        del _CACHE[fid]
