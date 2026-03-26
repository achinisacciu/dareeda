import polars as pl
from semantics.base import BaseDetector
from semantics.keywords import CATEGORICAL_KEYWORDS


class CategoricalDetector(BaseDetector):
    name = "categorical"

    def detect(self, df, col):
        score = 0.0
        col_lower = col.lower()
        meta = {}
        n_unique = None

        # 1. Match keyword nel nome
        for kw in CATEGORICAL_KEYWORDS:
            if col_lower == kw:
                score += 0.4
                break
            if kw in col_lower:
                score += 0.25
                break

        series = df[col]

        try:
            total = len(series)
            n_unique = series.n_unique()
            meta["n_unique"] = n_unique
            meta["total"] = total

            if total > 0:
                ratio = n_unique / total
                meta["unique_ratio"] = round(ratio, 4)

                # Bassa cardinalità = segnale forte di categorica
                if n_unique <= 2:
                    score += 0.2   # potrebbe essere booleano
                elif n_unique <= 10:
                    score += 0.4
                elif n_unique <= 20:
                    score += 0.3
                elif ratio < 0.05:
                    score += 0.2

        except Exception:
            pass

        # 2. Tipo stringa o categorico (Polars)
        if series.dtype in (pl.Utf8, pl.String, pl.Categorical):
            score += 0.3
        elif series.dtype == pl.Boolean:
            score += 0.5

        # 3. Penalizza se alta cardinalità su stringa (probabilmente testo libero)
        if series.dtype in (pl.Utf8, pl.String) and n_unique is not None:
            total = len(series)
            if total > 0 and (n_unique / total) > 0.5:
                score -= 0.3

        return {
            "semantic_type": "categorical",
            "confidence": min(max(score, 0.0), 1.0),
            "meta": {"n_unique": n_unique},
        }
