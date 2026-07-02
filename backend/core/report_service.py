"""
core/report_service.py

Servizio per la generazione di report PDF, isolato dallo strato HTTP.
Permette di mockare la dipendenza da Typst nei test.
"""

from __future__ import annotations

import io
import logging
from collections.abc import Callable

from core.report_generator import generate_report_in_memory

logger = logging.getLogger(__name__)


class ReportService:
    """
    Servizio che incapsula la logica di generazione PDF.

    La dipendenza da Typst è iniettabile via ``find_typst`` callback,
    in modo che i test possano fornire un mock senza toccare il filesystem.
    """

    def __init__(
        self,
        find_typst: Callable[[], str] | None = None,
    ) -> None:
        self._find_typst = find_typst

    def generate_pdf(self, analysis_data: dict) -> io.BytesIO:
        """
        Genera un PDF in memoria a partire dai dati di analisi.

        Parameters
        ----------
        analysis_data : dict
            Dizionario strutturato con i risultati dell'analisi EDA.

        Returns
        -------
        io.BytesIO
            Buffer contenente il PDF generato (posizionato all'inizio).
        """
        buffer = generate_report_in_memory(analysis_data)
        # buffer is already at seek(0) from generate_report_in_memory
        return buffer


# Istanza singleton per uso negli endpoint (la dipendenza Typst è quella reale)
report_service = ReportService()
