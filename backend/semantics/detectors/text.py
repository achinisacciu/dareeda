import polars as pl
from semantics.base import BaseDetector

TEXT_KEYWORDS = [
    # Inglese
    "description", "text", "notes", "note", "comment", "comments",
    "message", "body", "content", "summary", "detail", "details",
    "address", "street", "remark", "remarks", "feedback",
    "narrative", "reason", "explanation", "info", "information",
    "bio", "biography", "abstract", "review",
    # Italiano
    "descrizione", "testo", "nota", "commento", "messaggio",
    "contenuto", "sommario", "dettaglio", "indirizzo", "via",
    "motivo", "spiegazione", "informazione", "recensione",
    # Francese
    "description", "texte", "note", "commentaire", "message",
    "contenu", "adresse", "remarque", "explication", "avis",
    # Spagnolo
    "descripcion", "texto", "nota", "comentario", "mensaje",
    "contenido", "direccion", "motivo", "explicacion", "resena",
    # Tedesco
    "beschreibung", "text", "notiz", "kommentar", "nachricht",
    "inhalt", "adresse", "bemerkung", "erklarung",
]

# Lunghezza media minima (caratteri) per considerare testo libero
MIN_AVG_LENGTH = 25


class TextDetector(BaseDetector):
    name = "text"

    def detect(self, df, col):
        score = 0.0
        col_lower = col.lower()
        meta = {}

        # 1. Match keyword nel nome colonna
        for kw in TEXT_KEYWORDS:
            if col_lower == kw:
                score += 0.5
                break
            if kw in col_lower:
                score += 0.3
                break

        series = df[col]

        try:
            if series.dtype in (pl.Utf8, pl.String):
                score += 0.2

                non_null = series.drop_nulls()
                if len(non_null) > 0:
                    lengths = non_null.str.len_chars()
                    avg_len = lengths.mean()
                    max_len = lengths.max()
                    meta["avg_length"] = round(avg_len, 1) if avg_len else 0
                    meta["max_length"] = max_len

                    # Testo lungo = forte segnale di testo libero
                    if avg_len is not None:
                        if avg_len > 80:
                            score += 0.5
                        elif avg_len > MIN_AVG_LENGTH:
                            score += 0.35
                        elif avg_len > 10:
                            score += 0.1

                    # Alta cardinalità su stringa = testo libero (non categorico)
                    n_unique = non_null.n_unique()
                    total = len(non_null)
                    if total > 0 and (n_unique / total) > 0.7:
                        score += 0.1
                    meta["n_unique"] = n_unique

        except Exception:
            pass

        return {
            "semantic_type": "text",
            "confidence": min(score, 1.0),
            "meta": meta,
        }
