import uuid, json
import traceback
import threading
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from api.models.database import get_db, SessionLocal
from api.models.orm import AnalysisRun, ReportJob
from core.config import settings
from core.report_generator import generate_report

router = APIRouter()


def _bg_generate(report_id: str, analysis_id: str):
    db = SessionLocal()
    try:
        job = db.query(ReportJob).filter(ReportJob.id == report_id).first()
        run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
        if not job or not run:
            return
        with open(settings.data_dir / run.result_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        pdf_path   = generate_report(analysis_id, analysis_data, settings.reports_dir / analysis_id)
        job.status   = "completed"
        job.pdf_path = str(pdf_path.relative_to(settings.reports_dir))
        db.commit()
    except Exception as e:
        print(f"[REPORT ERROR] {traceback.format_exc()}")
        job = db.query(ReportJob).filter(ReportJob.id == report_id).first()
        if job:
            job.status = "failed"
            db.commit()
    finally:
        db.close()


@router.post("/generate/{analysis_id}", status_code=202)
def generate(analysis_id: str, db: Session = Depends(get_db)):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
    if not run:
        raise HTTPException(404, "Analisi non trovata")
    if run.status != "completed":
        raise HTTPException(409, "Analisi non ancora completata")
    rid = str(uuid.uuid4())
    db.add(ReportJob(id=rid, analysis_id=analysis_id, status="pending"))
    db.commit()
    threading.Thread(
        target=_bg_generate,
        args=(rid, analysis_id),
        name=f"dareeda-report-{rid}",
        daemon=True,
    ).start()
    return {"report_id": rid, "status": "pending"}


@router.get("/{report_id}/status")
def status(report_id: str, db: Session = Depends(get_db)):
    job = db.query(ReportJob).filter(ReportJob.id == report_id).first()
    if not job:
        raise HTTPException(404, "Report non trovato")
    return {"report_id": report_id, "status": job.status, "has_pdf": bool(job.pdf_path)}


@router.get("/{report_id}/download")
def download(report_id: str, db: Session = Depends(get_db)):
    job = db.query(ReportJob).filter(ReportJob.id == report_id).first()
    if not job:
        raise HTTPException(404, "Report non trovato")
    if job.status != "completed":
        raise HTTPException(409, f"Report non pronto: {job.status}")
    pdf = settings.reports_dir / job.pdf_path
    if not pdf.exists():
        raise HTTPException(500, "File PDF non trovato")
    return FileResponse(str(pdf), media_type="application/pdf",
                        filename=f"dareeda_report_{report_id[:8]}.pdf")
