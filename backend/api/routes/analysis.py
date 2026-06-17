"""
api/routes/analysis.py

Endpoints:
  POST /upload               — carica CSV/Parquet in cache, restituisce file_id
  POST /analyze/{file_id}    — esegue l'analisi in streaming (SSE), modulo per modulo
  DELETE /cache/{file_id}    — rimozione esplicita dalla cache (opzionale)
"""

import asyncio
import io
import json
import logging
import math
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
from core.file_cache import delete, get, store
from core.sampling import maybe_sample
from core.semantic_typer import group_by_semantic, type_dataframe
from eda.orchestrator import MODULES, _apply_single_action, _compute_accepted_features
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Costanti
# ─────────────────────────────────────────────────────────────────────────────

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────


class AnalysisRequest(BaseModel):
    """Body della richiesta POST /analyze/{file_id}."""

    target: str | None = None
    problem_type: str | None = None
    semantic_overrides: dict = Field(default_factory=dict)
    selected_features: list = Field(default_factory=list)
    accepted_features: list = Field(default_factory=list)
    cleaning_actions: list = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Utility: sanificazione JSON
# ─────────────────────────────────────────────────────────────────────────────


def _sanitize_for_json(obj: Any) -> Any:
    """
    Ricorsivamente sanifica un oggetto per la serializzazione JSON.
    Gestisce tipi numpy, NaN, Inf e altri tipi non serializzabili.
    """
    # bool va prima di int: in Python bool e' sottoclasse di int
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (float, np.floating, np.float64, np.float32)):
        if pd.isna(obj) or not math.isfinite(obj):
            return None
        return float(obj)
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, np.ndarray)):
        return [_sanitize_for_json(item) for item in obj]
    if obj is not None and not isinstance(obj, (int, str)):
        return str(obj)
    return obj


def _sse_event(event: str, data: dict) -> str:
    """Formatta un singolo evento SSE."""
    payload = json.dumps(_sanitize_for_json(data), ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


# ─────────────────────────────────────────────────────────────────────────────
# POST /upload
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/upload", status_code=200)
async def upload_file(file: UploadFile = File(...)):
    """
    Carica un file CSV o Parquet in memoria.
    Restituisce un file_id da usare con POST /analyze/{file_id}.
    """
    try:
        file_bytes = await file.read()

        if len(file_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File troppo grande: {len(file_bytes) / (1024 * 1024):.1f} MB. "
                f"Limite massimo: {MAX_UPLOAD_BYTES / (1024 * 1024):.0f} MB.",
            )

        file_buffer = io.BytesIO(file_bytes)
        filename = file.filename.lower()

        if filename.endswith(".csv"):
            df = pl.read_csv(file_buffer, ignore_errors=True)
        elif filename.endswith(".parquet"):
            df = pl.read_parquet(file_buffer)
        else:
            raise HTTPException(
                status_code=400, detail="Formato non supportato. Usa CSV o Parquet."
            )

        file_id = store(df, file.filename)

        return JSONResponse(
            content={
                "file_id": file_id,
                "filename": file.filename,
                "n_rows": df.height,
                "n_cols": df.width,
                "columns": df.columns,
                "dtypes": {
                    col: str(dtype) for col, dtype in zip(df.columns, df.dtypes, strict=False)
                },
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Errore durante il caricamento del file")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il caricamento: {str(e)}",
        ) from e


# ─────────────────────────────────────────────────────────────────────────────
# POST /analyze/{file_id}  — SSE streaming
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/analyze/{file_id}")
async def stream_analysis(file_id: str, body: AnalysisRequest):
    """
    Esegue l'analisi EDA in streaming (Server-Sent Events).
    Il client riceve un evento per ogni modulo completato.

    Formato eventi SSE emessi:
      event: start               — analisi avviata, metadati del run
      event: meta                — metadati del dataset
      event: feature_engineering — feature engineering e cleaning applicati
      event: module              — un modulo EDA completato  { module, label, data }
      event: done                — analisi completata
      event: error               — errore fatale              { detail }

    Body JSON:
      target, problem_type, semantic_overrides,
      selected_features, accepted_features, cleaning_actions
    """
    entry = get(file_id)
    if entry is None:
        raise HTTPException(
            status_code=404, detail="file_id non trovato o scaduto. Effettua nuovamente l'upload."
        )

    context = body.model_dump()
    df_full = entry["df"]
    filename = entry["filename"]

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # ── Evento iniziale ──────────────────────────────────────────────
            yield _sse_event(
                "start",
                {
                    "file_id": file_id,
                    "filename": filename,
                    "n_rows": df_full.height,
                    "n_cols": df_full.width,
                },
            )
            await asyncio.sleep(0)

            # ── Preprocessing + streaming per-modulo ─────────────────────────
            async for event_type, payload in _run_orchestrator_streaming(
                df_full, filename, context
            ):
                yield _sse_event(event_type, payload)
                await asyncio.sleep(0)

            # ── Fine ─────────────────────────────────────────────────────────
            yield _sse_event("done", {"status": "completed"})

        except Exception as e:
            logger.exception("Errore durante l'analisi streaming")
            yield _sse_event("error", {"detail": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _run_orchestrator_streaming(
    df_full: pl.DataFrame, filename: str, context: dict
) -> AsyncGenerator[tuple[str, dict], None]:
    """
    Esegue l'analisi EDA in vero streaming: ogni modulo viene eseguito
    separatamente via run_in_executor e il risultato viene emesso subito,
    senza attendere il completamento di tutti i moduli.
    """
    loop = asyncio.get_running_loop()

    # ── 1. Preprocessing (campionamento, feature engineering, cleaning, semantic typing) ──
    df, sampled, sample_n, semantic_types, groups, meta_info, fe_info = await loop.run_in_executor(
        None, _preprocess, df_full, filename, context
    )

    # ── 2. Emetti meta e feature_engineering ──
    yield ("meta", meta_info)
    yield ("feature_engineering", fe_info)

    # ── 3. Esegui ogni modulo singolarmente con streaming reale ──
    for key, label, fn in MODULES:
        try:
            if key in ("ml_exploratory", "multivariate"):
                result = await loop.run_in_executor(
                    None,
                    lambda f=fn, d=df, df_f=df_full, st=semantic_types, g=groups, c=context: f(
                        df=d, df_full=df_f, semantic_types=st, groups=g, context=c
                    ),
                )
            else:
                result = await loop.run_in_executor(
                    None,
                    lambda f=fn, d=df, df_f=df_full, st=semantic_types, g=groups: f(
                        df=d, df_full=df_f, semantic_types=st, groups=g
                    ),
                )

            yield (
                "module",
                {
                    "module": key,
                    "label": label,
                    "data": result,
                },
            )

        except Exception as e:
            logger.warning("Modulo %s fallito: %s", key, e)
            yield (
                "module",
                {
                    "module": key,
                    "label": label,
                    "data": {"error": str(e), "skipped": True},
                },
            )


def _preprocess(df_full: pl.DataFrame, filename: str, context: dict) -> tuple:
    """
    Esegue il preprocessing (campionamento, feature engineering, cleaning,
    semantic typing) e restituisce i dati pronti per i moduli EDA.

    Ritorna:
      (df, sampled, sample_n, semantic_types, groups, meta_info, fe_info)
    """
    start_time = datetime.now(UTC)

    # ── Campionamento ────────────────────────────────────────────────────────
    df, sampled, sample_n = maybe_sample(df_full)

    # ── Feature Engineering ──────────────────────────────────────────────────
    accepted_features: list[dict] = []
    for item in context.get("accepted_features", []):
        if isinstance(item, dict):
            accepted_features.append(item)
        elif isinstance(item, str):
            accepted_features.append({
                "name": item,
                "type": "unknown",
                "source_columns": [],
                "formula": "",
                "status": "accepted",
            })

    added_cols: list[str] = []
    if accepted_features:
        df, added_cols = _compute_accepted_features(df, accepted_features)
        df_full, _ = _compute_accepted_features(df_full, accepted_features)

    # ── Cleaning ─────────────────────────────────────────────────────────────
    pre_clean_rows = len(df_full)
    pre_clean_cols = len(df_full.columns)

    cleaning_actions = context.get("cleaning_actions") or []
    for act in cleaning_actions:
        df = _apply_single_action(df, act)
        df_full = _apply_single_action(df_full, act)

    cleaning_summary = {
        "actions": cleaning_actions,
        "before_rows": pre_clean_rows,
        "after_rows": len(df_full),
        "before_cols": pre_clean_cols,
        "after_cols": len(df_full.columns),
        "rows_removed": pre_clean_rows - len(df_full),
        "cols_removed": pre_clean_cols - len(df_full.columns),
    }

    # ── Semantic typing ──────────────────────────────────────────────────────
    semantic_types = type_dataframe(df)
    groups = group_by_semantic(semantic_types)

    runtime = max((datetime.now(UTC) - start_time).total_seconds(), 0.0)

    # ── Risultati preprocessing ──────────────────────────────────────────────
    meta_info = {
        "dataset_filename": filename,
        "generated_at": datetime.now(UTC).isoformat(),
        "target": context.get("target"),
        "problem_type": context.get("problem_type"),
        "n_rows_full": len(df_full),
        "n_cols": len(df_full.columns),
        "sampled": sampled,
        "sample_n": sample_n,
        "semantic_types": semantic_types,
        "runtime_seconds": runtime,
    }

    fe_info = {
        "accepted_features": accepted_features,
        "derived_columns": added_cols,
        "cleaning": cleaning_summary,
    }

    return df, sampled, sample_n, semantic_types, groups, meta_info, fe_info


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /cache/{file_id}  — pulizia esplicita (opzionale)
# ─────────────────────────────────────────────────────────────────────────────


@router.delete("/cache/{file_id}", status_code=200)
async def evict_cache(file_id: str):
    """
    Rimuove esplicitamente un file dalla cache in-memory.
    Utile se il frontend vuole liberare memoria subito dopo aver scaricato il report.
    """
    if get(file_id) is None:
        raise HTTPException(status_code=404, detail="file_id non trovato.")
    delete(file_id)
    return {"deleted": file_id}
