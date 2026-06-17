import polars as pl
from semantics.base import BaseDetector

DATE_KEYWORDS = [
    # Inglese
    "date",
    "time",
    "timestamp",
    "datetime",
    "created",
    "updated",
    "modified",
    "deleted",
    "day",
    "month",
    "year",
    "week",
    "hour",
    "start",
    "end",
    "begin",
    "expiry",
    "expiration",
    "due",
    "deadline",
    "birth",
    "dob",
    "shipped",
    "delivered",
    "ordered",
    "closed",
    # Italiano
    "data",
    "ora",
    "giorno",
    "mese",
    "anno",
    "settimana",
    "creato",
    "aggiornato",
    "inizio",
    "fine",
    "scadenza",
    "nascita",
    # Francese
    "date",
    "heure",
    "jour",
    "mois",
    "annee",
    "année",
    "debut",
    "fin",
    "echeance",
    "naissance",
    # Spagnolo
    "fecha",
    "hora",
    "dia",
    "mes",
    "ano",
    "año",
    "inicio",
    "fin",
    "vencimiento",
    "nacimiento",
    # Tedesco
    "datum",
    "zeit",
    "tag",
    "monat",
    "jahr",
    "beginn",
    "ende",
]

# Pattern regex-like per rilevamento date nelle stringhe
DATE_SEPARATORS = ("-", "/", ".")


class DateDetector(BaseDetector):
    name = "date"

    def detect(self, df, col):
        score = 0.0
        col_lower = col.lower()
        meta = {}

        # 1. Match keyword nel nome colonna
        for kw in DATE_KEYWORDS:
            if col_lower == kw:
                score += 0.5
                break
            if kw in col_lower:
                score += 0.35
                break

        series = df[col]

        try:
            # 2. Tipo data nativo Polars — segnale fortissimo
            if series.dtype in (pl.Date, pl.Datetime, pl.Time, pl.Duration):
                score += 0.6
                meta["dtype"] = str(series.dtype)

            # 3. Stringa che sembra una data (heuristic sul campione)
            elif series.dtype in (pl.Utf8, pl.String):
                sample = series.drop_nulls().head(20).to_list()
                if sample:
                    looks_like_date = sum(
                        1
                        for s in sample
                        if isinstance(s, str)
                        and any(sep in s for sep in DATE_SEPARATORS)
                        and any(c.isdigit() for c in s)
                        and len(s) >= 8
                    )
                    ratio = looks_like_date / len(sample)
                    if ratio > 0.8:
                        score += 0.4
                    elif ratio > 0.5:
                        score += 0.25
                    meta["sample_date_ratio"] = round(ratio, 2)

        except Exception:
            pass

        return {
            "semantic_type": "date",
            "confidence": min(score, 1.0),
            "meta": meta,
        }
