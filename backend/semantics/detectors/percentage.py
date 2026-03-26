import polars as pl
from semantics.base import BaseDetector

PERCENTAGE_KEYWORDS = [
    # Inglese
    "pct", "percent", "percentage", "rate", "ratio", "share",
    "prob", "probability", "proportion", "fraction", "perc",
    "utilization", "utilisation", "coverage", "fill",
    "growth", "change", "delta", "variance", "margin",
    # Italiano
    "percentuale", "tasso", "quota", "proporzione",
    "probabilità", "probabilita", "variazione", "crescita",
    # Francese
    "pourcentage", "taux", "part", "proportion", "croissance",
    # Spagnolo
    "porcentaje", "tasa", "proporcion", "probabilidad", "crecimiento",
    # Tedesco
    "prozent", "anteil", "rate", "wahrscheinlichkeit",
]

NUMERIC_DTYPES = (
    pl.Int8, pl.Int16, pl.Int32, pl.Int64,
    pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
    pl.Float32, pl.Float64,
)


class PercentageDetector(BaseDetector):
    name = "percentage"

    def detect(self, df, col):
        score = 0.0
        col_lower = col.lower()
        meta = {}

        # 1. Simbolo % nel nome — segnale fortissimo
        if "%" in col:
            score += 0.6

        # 2. Match keyword nel nome colonna
        if score == 0.0:
            for kw in PERCENTAGE_KEYWORDS:
                if col_lower == kw:
                    score += 0.45
                    break
                if kw in col_lower:
                    score += 0.3
                    break

        series = df[col]

        # 3. Analisi valori (Polars-style)
        if series.dtype in NUMERIC_DTYPES:
            score += 0.1

            try:
                non_null = series.drop_nulls()
                if len(non_null) > 0:
                    smin = float(non_null.min())
                    smax = float(non_null.max())
                    meta["min"] = smin
                    meta["max"] = smax

                    # Range 0-1 (proporzione decimale)
                    if smin >= 0.0 and smax <= 1.0:
                        score += 0.45
                        meta["scale"] = "0-1"

                    # Range 0-100 (percentuale classica)
                    elif smin >= 0.0 and smax <= 100.0:
                        score += 0.35
                        meta["scale"] = "0-100"

                    # Range -100/100 (variazione percentuale)
                    elif smin >= -100.0 and smax <= 100.0:
                        score += 0.2
                        meta["scale"] = "-100/100"

            except Exception:
                pass

        return {
            "semantic_type": "percentage",
            "confidence": min(score, 1.0),
            "meta": meta,
        }
