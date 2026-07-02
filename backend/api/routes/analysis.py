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
import tempfile
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
from core.config import settings
from core.file_cache import delete, get, store, store_parquet
import functools
from core.models import AcceptedFeature, AnalysisRequest, CleaningAction
from core.sampling import maybe_sample
from core.semantic_typer import group_by_semantic, type_dataframe
from eda.orchestrator import MODULES, _apply_single_action, _compute_accepted_features
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Costanti e Mapping Ruoli
# ─────────────────────────────────────────────────────────────────────────────

MAX_UPLOAD_BYTES = settings.max_upload_bytes  # config-driven

ROLE_MODULES = {
    "data_scientist": {"overview", "bivariate", "multivariate", "timeseries", "ml_exploratory", "inference"},
    "ml_engineer": {"overview", "data_quality", "multivariate", "ml_exploratory"},
    "data_analyst": {"overview", "data_quality", "univariate", "bivariate", "timeseries"},
}

_POLARS_SEMAPHORE = asyncio.Semaphore(4)


# ─────────────────────────────────────────────────────────────────────────────
# Utility: sanificazione JSON
# ─────────────────────────────────────────────────────────────────────────────


def _sanitize_for_json(obj: Any) -> Any:
    """
    Ricorsivamente sanifica un oggetto per la serializzazione JSON.
    Gestisce tipi numpy, NaN, Inf e altri tipi non serializzabili.
    """
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, np.floating):
        if pd.isna(obj) or not math.isfinite(obj):
            return None
        return float(obj)
    if isinstance(obj, float):
        if pd.isna(obj) or not math.isfinite(obj):
            return None
        return float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, int):
        return int(obj)
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, np.ndarray)):
        return [_sanitize_for_json(item) for item in obj]
    if obj is not None and not isinstance(obj, str):
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
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename mancante")
        filename = file.filename.lower()

        # ponytail: SpooledTemporaryFile scrive su disco oltre 10MB, non accumula in RAM
        CHUNK_SIZE = 1024 * 1024  # 1 MB
        with tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024) as spool:
            size = 0
            while chunk := await file.read(CHUNK_SIZE):
                spool.write(chunk)
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File troppo grande. Limite massimo: {MAX_UPLOAD_BYTES / (1024 * 1024):.0f} MB.",
                    )
            spool.seek(0)
    
            loop = asyncio.get_running_loop()
            if filename.endswith(".csv"):
                # ponytail: pl.read_csv in executor per non bloccare l'event loop
                # ponytail: ignore_errors=False, dati corrotti → errore 422, non analisi falsata
                df = await loop.run_in_executor(
                    None, lambda: pl.read_csv(spool, ignore_errors=False)
                )
            elif filename.endswith(".parquet"):
                df = await loop.run_in_executor(None, lambda: pl.read_parquet(spool))
            else:
                raise HTTPException(
                    status_code=400, detail="Formato non supportato. Usa CSV o Parquet."
                )
    
        file_id = store_parquet(df, filename)

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
        # ponytail: logga il dettaglio, non leakare l'infrastruttura al client
        raise HTTPException(
            status_code=500,
            detail="Errore interno del server durante la lettura del file.",
        ) from e


# ─────────────────────────────────────────────────────────────────────────────
# POST /analyze/{file_id}  — SSE streaming
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/analyze/{file_id}")
async def stream_analysis(file_id: str, body: AnalysisRequest, role: str | None = None):
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
    df_full = entry["df"].clone()
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
            # ponytail: yield cede il controllo in Python 3.11+, asyncio.sleep(0) inutile

            # ── Preprocessing + streaming per-modulo ─────────────────────────
            async for event_type, payload in _run_orchestrator_streaming(
                df_full, filename, context, role
            ):
                yield _sse_event(event_type, payload)

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
    df_full: pl.DataFrame, filename: str, context: dict, role: str | None = None
) -> AsyncGenerator[tuple[str, dict], None]:
    """
    Esegue l'analisi EDA in vero streaming: ogni modulo viene eseguito
    separatamente via run_in_executor e il risultato viene emesso subito,
    senza attendere il completamento di tutti i moduli.
    """
    loop = asyncio.get_running_loop()

    if role:
        role = role.lower()
    allowed_modules = ROLE_MODULES.get(role) if role in ROLE_MODULES else None

    # ── 1. Preprocessing (campionamento, feature engineering, cleaning, semantic typing) ──
    async with _POLARS_SEMAPHORE:
        df, sampled, sample_n, semantic_types, groups, meta_info, fe_info = await loop.run_in_executor(
            None, _preprocess, df_full, filename, context
        )

    # ── 2. Emetti meta e feature_engineering ──
    yield ("meta", meta_info)
    yield ("feature_engineering", fe_info)

    # ── 3. Esegui ogni modulo singolarmente con streaming reale ──


    for key, label, fn in MODULES:
        if allowed_modules and key not in allowed_modules:
            continue
            
        try:
            async with _POLARS_SEMAPHORE:
                if key in ("ml_exploratory", "multivariate"):
                    func = functools.partial(
                        fn, df=df, df_full=df_full, semantic_types=semantic_types, groups=groups, context=context
                    )
                else:
                    func = functools.partial(
                        fn, df=df, df_full=df_full, semantic_types=semantic_types, groups=groups
                    )
                result = await loop.run_in_executor(None, func)

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
    Esegue il preprocessing (feature engineering, cleaning, campionamento,
    semantic typing) e restituisce i dati pronti per i moduli EDA.

    Ponytail: applica le trasformazioni solo a df_full, poi ricampiona.
    Evita memory explosion e desincronizzazione tra df e df_full.

    Ritorna:
      (df, sampled, sample_n, semantic_types, groups, meta_info, fe_info)
    """
    start_time = datetime.now(UTC)

    # ── Feature Engineering ──────────────────────────────────────────────────
    accepted_features: list[AcceptedFeature] = []
    for item in context.get("accepted_features", []):
        accepted_features.append(
            AcceptedFeature.model_validate(item) if isinstance(item, dict) else item
        )

    added_cols: list[str] = []
    if accepted_features:
        df_full, added_cols, _ = _compute_accepted_features(df_full, accepted_features)

    # ── Cleaning ─────────────────────────────────────────────────────────────
    pre_clean_rows = len(df_full)
    pre_clean_cols = len(df_full.columns)

    cleaning_actions_raw = context.get("cleaning_actions") or []
    cleaning_actions: list[CleaningAction] = [
        CleaningAction.model_validate(act) if isinstance(act, dict) else act
        for act in cleaning_actions_raw
    ]
    for act in cleaning_actions:
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

    # ── Campionamento (dopo trasformazioni) ──────────────────────────────────
    df, sampled, sample_n = maybe_sample(df_full)

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


# ─────────────────────────────────────────────────────────────────────────────
# POST /export/{file_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/export/{file_id}")
async def export_code(file_id: str, body: AnalysisRequest):
    """
    Genera un file Python riproducibile (snippet Polars) in base
    alle azioni di cleaning e feature engineering applicate.
    """
    entry = get(file_id)
    if entry is None:
        raise HTTPException(
            status_code=404, detail="file_id non trovato. Effettua l'upload."
        )

    context = body.model_dump()
    filename = entry["filename"]
    
    lines = [
        'import polars as pl',
        '',
        f'# 1. Caricamento Dati',
        f'# Assicurati di avere il file {json.dumps(filename)} nella directory corretta.',
        f'df = pl.read_csv({json.dumps(filename)}) if {json.dumps(filename)}.endswith(".csv") else pl.read_parquet({json.dumps(filename)})',
        ''
    ]
    
    # Feature Engineering
    accepted_features = context.get("accepted_features", [])
    if accepted_features:
        lines.append('# 2. Feature Engineering')
        for f in accepted_features:
            name = f.get('name') if isinstance(f, dict) else getattr(f, 'name', '')
            formula = f.get('formula') if isinstance(f, dict) else getattr(f, 'formula', '')
            if name and formula:
                # Per semplicità, creiamo un placeholder commentato,
                # dato che la logica nel backend non sempre ha traduzione banale in codice raw 1:1,
                # ma per ratio/margin è semplice. Mostriamo la descrizione.
                lines.append(f'# Feature: {name} (Formula: {formula})')
                lines.append(f'# Implementazione dipende dal tipo. Vedi logica backend in orchestrator.py')
        lines.append('')
        
    # Cleaning
    cleaning_actions = context.get("cleaning_actions", [])
    if cleaning_actions:
        lines.append('# 3. Data Cleaning')
        for act in cleaning_actions:
            act_type = act.get('type') if isinstance(act, dict) else getattr(act, 'type', '')
            col = act.get('column') if isinstance(act, dict) else getattr(act, 'column', '')
            
            if act_type == "drop_duplicate_rows":
                lines.append('df = df.unique(maintain_order=True)')
            elif act_type == "exclude_column" and col:
                lines.append(f'if "{col}" in df.columns: df = df.drop("{col}")')
            elif act_type == "trim_whitespace" and col:
                lines.append(f'df = df.with_columns(pl.when(pl.col("{col}").is_null()).then(pl.lit(None, dtype=pl.String)).otherwise(pl.col("{col}").str.strip_chars()).alias("{col}"))')
        lines.append('')
        
    lines.extend([
        '# 4. Dati pronti per la modellazione',
        'print("Shape:", df.shape)',
        'print(df.head())'
    ])
    
    script_content = "\n".join(lines)
    
    # Ritorna come testo semplice Python
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=script_content, media_type="text/x-python")
