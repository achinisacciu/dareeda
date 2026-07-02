import logging
from typing import Any

from core.report_service import report_service
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class ReportRequest(BaseModel):
    analysis_data: dict[str, Any]


import asyncio

@router.post("/generate-pdf", summary="Genera un PDF in memoria e lo restituisce direttamente")
async def generate_pdf_stateless(payload: ReportRequest):
    try:
        loop = asyncio.get_running_loop()
        pdf_buffer = await loop.run_in_executor(
            None, report_service.generate_pdf, payload.analysis_data
        )
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()

        headers = {"Content-Disposition": 'attachment; filename="dareeda_report.pdf"'}
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Errore generazione report")
        raise HTTPException(
            status_code=500,
            detail="Errore durante la generazione del report PDF",
        ) from e
