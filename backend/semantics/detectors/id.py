import polars as pl
from semantics.base import BaseDetector
from semantics.keywords import ID_KEYWORDS


class IDDetector(BaseDetector):
    name = "id"

    def detect(self, df, col):
        score = 0.0
        col_lower = col.lower()
        meta = {}

        # 1. Match keyword — controlla prima pattern prefisso/suffisso
        prefix_suffix_patterns = ["_id", "id_", "_key", "key_", "_code", "code_", "_cod", "cod_"]
        for pattern in prefix_suffix_patterns:
            if col_lower.startswith(pattern.lstrip("_")) or col_lower.endswith(pattern.lstrip("_")):
                score += 0.5
                break

        # 2. Match esatto o contenuto
        if score == 0.0:
            for kw in ID_KEYWORDS:
                if col_lower == kw:
                    score += 0.55
                    break
                if kw in col_lower:
                    score += 0.35
                    break

        series = df[col]

        try:
            n_unique = series.n_unique()
            total = len(series)
            meta["n_unique"] = n_unique
            meta["total"] = total

            if total > 0:
                ratio = n_unique / total
                meta["unique_ratio"] = round(ratio, 4)

                # Alta cardinalità = segnale forte di ID
                if ratio > 0.95:
                    score += 0.4
                elif ratio > 0.8:
                    score += 0.25
                elif ratio > 0.6:
                    score += 0.1

                # Tutte righe uniche = quasi certamente un ID
                if n_unique == total:
                    score += 0.1

        except Exception:
            meta["unique_ratio"] = 0.0

        # 3. Penalizza se numerico con pochi valori unici (non è un ID)
        numeric_dtypes = (pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                          pl.Float32, pl.Float64)
        if series.dtype in numeric_dtypes:
            try:
                if series.n_unique() < 20:
                    score -= 0.3
            except Exception:
                pass

        return {
            "semantic_type": "id",
            "confidence": min(max(score, 0.0), 1.0),
            "meta": meta,
        }
