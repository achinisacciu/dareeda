import traceback
from typing import Any

# Sostituisci questo con il tuo vero import per la generazione PDF
from core.report_generator import generate_report_in_memory
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

router = APIRouter()

# Schema per accettare l'output JSON dell'analisi dal frontend
class ReportRequest(BaseModel):
    analysis_data: dict[str, Any]

@router.post("/generate-pdf", summary="Genera un PDF in memoria e lo restituisce direttamente")
def generate_pdf_stateless(payload: ReportRequest):
    try:
        # Invece di scrivere su disco, la tua funzione generate_report
        # deve essere adattata per restituire un oggetto io.BytesIO() o i bytes del PDF

        pdf_buffer = generate_report_in_memory(payload.analysis_data)

        # Recupera i bytes generati
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()

        # Restituisce direttamente il file PDF al browser senza salvarlo
        headers = {
            'Content-Disposition': 'attachment; filename="dareeda_report.pdf"'
        }
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers=headers
        )

    except Exception:
        print(f"[REPORT ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Errore durante la generazione del report PDF")
