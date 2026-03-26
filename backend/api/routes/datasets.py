import uuid
import json
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from api.models.database import get_db
from api.models.orm import Dataset, Project
from api.models.schemas import DatasetResponse
from core.config import settings
from core.data_loader import load_file, get_memory_mb, get_preview
from core.sampling import maybe_sample, get_sample_info
from core.semantic_typer import type_dataframe, group_by_semantic
from pydantic import BaseModel
from typing import List

router = APIRouter()

ALLOWED_EXT = {".csv", ".xlsx", ".xls", ".json"}


# ── Schema per approvazione misure ──────────────────────────────────────────

class FeatureDecision(BaseModel):
    name: str
    status: str  # "accepted" | "rejected"


class FeatureDecisionsPayload(BaseModel):
    decisions: List[FeatureDecision]


# ── Upload ───────────────────────────────────────────────────────────────────

@router.post("/upload", status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    project_id: str  = Form(...),
    db: Session      = Depends(get_db),
):
    # Verifica progetto
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Progetto non trovato")

    # Verifica estensione
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Formato non supportato: {ext}. Usa CSV, XLSX o JSON.")

    # Salva file su disco
    dataset_id = str(uuid.uuid4())
    dest_dir   = settings.data_dir / project_id / "raw"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path  = dest_dir / f"{dataset_id}{ext}"

    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Carica con Polars
    try:
        df_full = load_file(dest_path)
    except Exception as e:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(422, f"Errore lettura file: {str(e)}")

    n_rows_full = len(df_full)
    n_cols      = len(df_full.columns)
    memory_mb   = get_memory_mb(df_full)

    # Campionamento
    df, sampled, sample_n = maybe_sample(df_full)

    # Tipi semantici (vecchio sistema, mantenuto per compatibilità)
    semantic_types = type_dataframe(df)
    groups         = group_by_semantic(semantic_types)

    # Motore semantico
    from semantics.engine import analyze_dataset
    sem_analysis = analyze_dataset(df)

    # Misure suggerite — inizialmente tutte "pending"
    suggested_features = sem_analysis.get("suggested_features", [])
    for f in suggested_features:
        f["status"] = "pending"

    # Anteprima
    preview = get_preview(df_full, n=20)

    # Colonne struttura
    col_info = []
    for col in df_full.columns:
        s = df_full[col]
        n_null   = s.null_count()
        col_sem  = sem_analysis["columns"].get(col, {})
        sem_type = col_sem.get("semantic_type", "unknown")
        if sem_type == "unknown":
            sem_type = semantic_types.get(col, "unknown")

        col_info.append({
            "name":           col,
            "dtype_original": str(s.dtype),
            "semantic_type":  sem_type,
            "confidence":     col_sem.get("confidence", 0.0),
            "n_unique":       s.drop_nulls().n_unique(),
            "pct_missing":    round(n_null / n_rows_full * 100, 2) if n_rows_full > 0 else 0.0,
        })

    # Salva nel DB (suggested_features serializzate come JSON)
    record = Dataset(
        id                 = dataset_id,
        project_id         = project_id,
        filename           = file.filename,
        filepath           = str(dest_path.relative_to(settings.data_dir)),
        file_format        = ext.lstrip("."),
        n_rows             = n_rows_full,
        n_cols             = n_cols,
        memory_mb          = memory_mb,
        sampled            = sampled,
        sample_n           = sample_n,
        suggested_features = json.dumps(suggested_features, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "dataset_id":         dataset_id,
        "filename":           file.filename,
        "file_format":        ext.lstrip("."),
        "n_rows":             n_rows_full,
        "n_cols":             n_cols,
        "memory_mb":          memory_mb,
        "sampled":            sampled,
        "sample_n":           sample_n,
        "sample_info":        get_sample_info(n_rows_full),
        "columns":            col_info,
        "suggested_features": suggested_features,
        "groups":             groups,
        "preview":            preview,
    }


# ── Approvazione / rifiuto misure ────────────────────────────────────────────

@router.get("/{dataset_id}/suggested-features")
def get_suggested_features(dataset_id: str, db: Session = Depends(get_db)):
    """Restituisce le misure suggerite con il loro status attuale."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset non trovato")

    features = json.loads(ds.suggested_features) if ds.suggested_features else []
    return {
        "dataset_id": dataset_id,
        "suggested_features": features,
        "total": len(features),
        "pending":  sum(1 for f in features if f.get("status") == "pending"),
        "accepted": sum(1 for f in features if f.get("status") == "accepted"),
        "rejected": sum(1 for f in features if f.get("status") == "rejected"),
    }


@router.patch("/{dataset_id}/suggested-features")
def update_feature_decisions(
    dataset_id: str,
    payload: FeatureDecisionsPayload,
    db: Session = Depends(get_db),
):
    """Aggiorna lo status (accepted/rejected) di una o più misure suggerite."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset non trovato")

    features = json.loads(ds.suggested_features) if ds.suggested_features else []

    # Valida i valori di status
    valid_statuses = {"accepted", "rejected", "pending"}
    for d in payload.decisions:
        if d.status not in valid_statuses:
            raise HTTPException(400, f"Status non valido: '{d.status}'. Usa: accepted, rejected, pending.")

    # Aggiorna le decisioni per nome
    decision_map = {d.name: d.status for d in payload.decisions}
    updated = []
    not_found = []

    for feature in features:
        name = feature.get("name")
        if name in decision_map:
            feature["status"] = decision_map[name]
            updated.append(name)
        feature_names_in_payload = {d.name for d in payload.decisions}

    not_found = [name for name in decision_map if name not in [f.get("name") for f in features]]

    ds.suggested_features = json.dumps(features, ensure_ascii=False)
    db.commit()

    return {
        "dataset_id": dataset_id,
        "updated": updated,
        "not_found": not_found,
        "suggested_features": features,
    }


@router.post("/{dataset_id}/suggested-features/accept-all")
def accept_all_features(dataset_id: str, db: Session = Depends(get_db)):
    """Accetta tutte le misure pending in un colpo solo."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset non trovato")

    features = json.loads(ds.suggested_features) if ds.suggested_features else []
    for f in features:
        if f.get("status") == "pending":
            f["status"] = "accepted"

    ds.suggested_features = json.dumps(features, ensure_ascii=False)
    db.commit()

    return {"dataset_id": dataset_id, "accepted": len(features), "suggested_features": features}


@router.post("/{dataset_id}/suggested-features/reject-all")
def reject_all_features(dataset_id: str, db: Session = Depends(get_db)):
    """Rifiuta tutte le misure pending."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset non trovato")

    features = json.loads(ds.suggested_features) if ds.suggested_features else []
    for f in features:
        if f.get("status") == "pending":
            f["status"] = "rejected"

    ds.suggested_features = json.dumps(features, ensure_ascii=False)
    db.commit()

    return {"dataset_id": dataset_id, "rejected": len(features), "suggested_features": features}


# ── Endpoint esistenti ───────────────────────────────────────────────────────

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset non trovato")
    return ds


@router.get("/{dataset_id}/preview")
def get_dataset_preview(dataset_id: str, n: int = 20, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset non trovato")
    path = settings.data_dir / ds.filepath
    df   = load_file(path)
    return {"preview": get_preview(df, n=min(n, 100))}


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset non trovato")
    db.delete(ds)
    db.commit()
