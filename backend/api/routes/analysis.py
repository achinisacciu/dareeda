import uuid
import math
import json
import re
import numbers
import threading
import polars as pl
from fastapi.responses import Response
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.models.database import get_db
from api.models.orm import AnalysisRun, Dataset
from api.models.schemas import AnalysisStatusResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from core.config import settings
from core.data_loader import load_file
from core.sampling import maybe_sample
from eda.orchestrator import run_analysis


class AnalysisRequest(BaseModel):
    target:             Optional[str]            = None
    problem_type:       Optional[str]            = None
    semantic_overrides: Optional[Dict[str, str]] = {}
    selected_features:  Optional[List[str]]      = []
    accepted_features:  Optional[List[str]]      = []  # feature derivate accettate
    # Azioni di pulizia selezionate dall'utente (fase 2/3)
    # Struttura minima:
    # - { "type": "exclude_column", "column": "<col>" , "params": {...} }
    # - { "type": "drop_duplicate_rows", "params": {...} }
    # - { "type": "replace_values", "column": "<col>", "params": {"match_mode": "...", "values": [...], "replacement": null} }
    # - { "type": "trim_whitespace", "column": "<col>", "params": {} }
    cleaning_actions:   Optional[List[Dict]]    = []


router = APIRouter()


@router.post("/run/{dataset_id}", status_code=202)
def start_analysis(
    dataset_id: str,
    payload: AnalysisRequest,
    db: Session = Depends(get_db),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset non trovato")

    analysis_id = str(uuid.uuid4())
    run = AnalysisRun(
        id         = analysis_id,
        dataset_id = dataset_id,
        status     = "pending",
        progress_pct = 0,
    )
    db.add(run)
    db.commit()

    from api.models.database import SessionLocal

    def bg_task():
        bg_db = SessionLocal()
        context = {
            "target":             payload.target,
            "problem_type":       payload.problem_type,
            "semantic_overrides": payload.semantic_overrides,
            "selected_features":  payload.selected_features,
            "accepted_features":  payload.accepted_features,
            "cleaning_actions":   payload.cleaning_actions,
        }
        try:
            run_analysis(analysis_id, dataset_id, bg_db, context=context)
        finally:
            bg_db.close()

    threading.Thread(
        target=bg_task,
        name=f"dareeda-analysis-{analysis_id}",
        daemon=True,
    ).start()
    return {"analysis_id": analysis_id, "status": "pending", "message": "Analisi avviata"}


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
def get_status(analysis_id: str, db: Session = Depends(get_db)):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
    if not run:
        raise HTTPException(404, "Analisi non trovata")
    return run


@router.get("/{analysis_id}/results")
def get_results(analysis_id: str, db: Session = Depends(get_db)):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
    if not run:
        raise HTTPException(404, "Analisi non trovata")
    if run.status != "completed":
        raise HTTPException(409, f"Analisi non completata. Stato attuale: {run.status}")

    result_path = settings.data_dir / run.result_path
    if not result_path.exists():
        raise HTTPException(500, "File risultati non trovato")

    with open(result_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r'\bNaN\b', 'null', content)
    content = re.sub(r'\bInfinity\b', 'null', content)
    content = re.sub(r'\b-Infinity\b', 'null', content)

    return Response(content=content, media_type="application/json")


@router.get("/{analysis_id}/section/{section}")
def get_section(analysis_id: str, section: str, db: Session = Depends(get_db)):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
    if not run:
        raise HTTPException(404, "Analisi non trovata")
    if run.status != "completed":
        raise HTTPException(409, f"Analisi non completata. Stato: {run.status}")

    result_path = settings.data_dir / run.result_path
    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if section not in data:
        raise HTTPException(404, f"Sezione '{section}' non trovata. Disponibili: {list(data.keys())}")
    return {section: data[section]}


@router.get("/{analysis_id}/sample-data")
def get_sample_data(
    analysis_id: str,
    columns: str = "",
    includeTarget: bool = False,
    db: Session = Depends(get_db),
):
    """
    Restituisce valori campionati per colonne selezionate.
    Usato da `Multivariata` per costruire grafici client-side.
    """
    run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
    if not run:
        raise HTTPException(404, "Analisi non trovata")
    if run.status != "completed":
        raise HTTPException(409, f"Analisi non completata. Stato: {run.status}")

    dataset = db.query(Dataset).filter(Dataset.id == run.dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset non trovato")

    sample_path = settings.data_dir / dataset.project_id / f"analysis_{analysis_id}_sample.parquet"
    df_sample = None
    if sample_path.exists():
        try:
            df_sample = pl.read_parquet(sample_path)
        except Exception:
            df_sample = None

    requested_cols = [c.strip() for c in columns.split(",") if c.strip()] if columns else []

    try:
        if df_sample is None:
            # Fallback: se non c'è parquet (o scrittura/parquet non disponibile),
            # carichiamo il dataset e applichiamo lo stesso campionamento del backend.
            filepath = settings.data_dir / dataset.filepath
            df_full = load_file(filepath)
            df_sample, _, _ = maybe_sample(df_full)
    except Exception as e:
        raise HTTPException(500, f"Errore caricamento sample: {str(e)}")

    missing_requested = [c for c in requested_cols if c not in df_sample.columns]
    if missing_requested:
        try:
            filepath = settings.data_dir / dataset.filepath
            df_full = load_file(filepath)
            df_sample, _, _ = maybe_sample(df_full)
        except Exception as e:
            raise HTTPException(500, f"Errore caricamento sample completo: {str(e)}")

    selected_cols = [c for c in requested_cols if c in df_sample.columns]

    def _sanitize(values):
        out = []
        for v in values:
            if v is None:
                out.append(None)
            elif isinstance(v, numbers.Number):
                # Gestione NaN/Inf
                if not math.isfinite(float(v)):
                    out.append(None)
                else:
                    # Converti a float python per evitare problemi di serializzazione JSON
                    fv = float(v)
                    if fv.is_integer():
                        out.append(int(fv))
                    else:
                        out.append(fv)
            else:
                out.append(v)
        return out

    payload = {"columns": {}}
    for c in selected_cols:
        payload["columns"][c] = _sanitize(df_sample[c].to_list())

    if includeTarget:
        # Il nome target lo prendiamo dalla sezione multivariata salvata nell'analysis json
        target_col = None
        try:
            result_path = settings.data_dir / run.result_path
            with open(result_path, "r", encoding="utf-8") as f:
                analysis_json = json.load(f)
            target_col = analysis_json.get("multivariate", {}).get("target")
        except Exception:
            target_col = None

        if target_col and target_col in df_sample.columns:
            payload["target"] = {
                "column": target_col,
                "values": _sanitize(df_sample[target_col].to_list()),
            }
        else:
            payload["target"] = None
    return payload
