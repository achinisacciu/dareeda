"""
core/file_cache.py

Cache in-memory per i DataFrame caricati via upload.
Mappa file_id -> { "df": pl.DataFrame, "filename": str, "uploaded_at": datetime }

In produzione sostituire con Redis + serializzazione Arrow/Parquet.
"""

import heapq
import io
import threading
import uuid
from datetime import UTC, datetime, timedelta

import polars as pl

from core.config import settings


def _ttl() -> int:
    return getattr(settings, 'upload_ttl_minutes', _TTL_MINUTES)

# Dizionario principale: { file_id: { df, filename, uploaded_at } }
_CACHE: dict[str, dict] = {}

# Heap (cutoff, file_id) per evict O(log n) invece di O(n) su store/get
_EXPIRY: list[tuple[datetime, str]] = []
_EXPIRY_SET: set[str] = set()

# ponytail: threading.Lock per thread-safety reale con run_in_executor
_CACHE_LOCK = threading.Lock()

_TTL_MINUTES = 30
# ponytail: limite massimo entry per evitare memory leak sotto carico
_MAX_CACHE_ENTRIES = 50


def store(df: pl.DataFrame, filename: str) -> str:
    """Salva un DataFrame nella cache e restituisce il file_id generato."""
    with _CACHE_LOCK:
        _evict_expired()
        # ponytail: se la cache è piena, rimuovi la più vecchia
        while len(_CACHE) >= _MAX_CACHE_ENTRIES and _EXPIRY:
            _expired, fid = heapq.heappop(_EXPIRY)
            _EXPIRY_SET.discard(fid)
            _CACHE.pop(fid, None)
        file_id = str(uuid.uuid4())
        _CACHE[file_id] = {
            "df": df,
            "filename": filename,
            "uploaded_at": datetime.now(UTC),
        }
        cutoff = datetime.now(UTC) + timedelta(minutes=_ttl())
        heapq.heappush(_EXPIRY, (cutoff, file_id))
        _EXPIRY_SET.add(file_id)
    return file_id


def get(file_id: str) -> dict | None:
    """
    Recupera la entry dalla cache.
    Restituisce None se non esiste o se è scaduta.
    """
    with _CACHE_LOCK:
        _evict_expired()
        entry = _CACHE.get(file_id)
        if not entry:
            return None
            
    result = dict(entry)
    if result.get("df") is None and result.get("parquet") is not None:
        result["df"] = pl.read_parquet(io.BytesIO(result["parquet"]))
    return result


def store_parquet(df: pl.DataFrame, filename: str) -> str:
    """Salva un DataFrame serializzato in Parquet (più compatto, veloce da rileggere)."""
    with _CACHE_LOCK:
        _evict_expired()
        # ponytail: stessa evizione di store() per non bypassare il limite massimo
        while len(_CACHE) >= _MAX_CACHE_ENTRIES and _EXPIRY:
            _expired, fid = heapq.heappop(_EXPIRY)
            _EXPIRY_SET.discard(fid)
            _CACHE.pop(fid, None)
        file_id = str(uuid.uuid4())
        _CACHE[file_id] = {
            "df": None,
            "parquet": df.write_parquet(),  # type: ignore[call-arg]  # noqa: E501
            "filename": filename,
            "uploaded_at": datetime.now(UTC),
        }
        cutoff = datetime.now(UTC) + timedelta(minutes=_ttl())
        heapq.heappush(_EXPIRY, (cutoff, file_id))
        _EXPIRY_SET.add(file_id)
    return file_id


def delete(file_id: str) -> None:
    """Rimuove esplicitamente un file dalla cache."""
    with _CACHE_LOCK:
        _CACHE.pop(file_id, None)
        _EXPIRY_SET.discard(file_id)


def _evict_expired() -> None:
    """Rimuove le entry più vecchie del TTL, early-exit quando la heap raggiunge una entry valida."""
    now = datetime.now(UTC)
    while _EXPIRY and _EXPIRY[0][0] <= now:
        _expiry, fid = heapq.heappop(_EXPIRY)
        if fid not in _EXPIRY_SET:
            continue
        _EXPIRY_SET.discard(fid)
        _CACHE.pop(fid, None)
