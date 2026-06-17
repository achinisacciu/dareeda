import polars as pl
from semantics.base import BaseDetector
from semantics.keywords import PRICE_KEYWORDS


class PriceDetector(BaseDetector):
    name = "price"

    NUMERIC_DTYPES = (
        pl.Int8,
        pl.Int16,
        pl.Int32,
        pl.Int64,
        pl.UInt8,
        pl.UInt16,
        pl.UInt32,
        pl.UInt64,
        pl.Float32,
        pl.Float64,
    )

    def detect(self, df, col):
        score = 0.0
        col_lower = col.lower()
        meta = {}

        # 1. Match keyword nel nome colonna (peso maggiore per match esatto)
        for kw in PRICE_KEYWORDS:
            if col_lower == kw:
                score += 0.6
                break
            if kw in col_lower:
                score += 0.4
                break

        series = df[col]

        # 2. Tipo numerico (Polars-style)
        if series.dtype in self.NUMERIC_DTYPES:
            score += 0.2

            try:
                non_null = series.drop_nulls()

                if len(non_null) > 0:
                    smin = non_null.min()
                    smax = non_null.max()
                    sstd = non_null.std()
                    n_unique = non_null.n_unique()

                    meta["min"] = smin
                    meta["max"] = smax
                    meta["n_unique"] = n_unique

                    # 3. Valori positivi (tipico dei prezzi)
                    if smin is not None and smin >= 0:
                        score += 0.1

                    # 4. Distribuzione non binaria
                    if n_unique > 10:
                        score += 0.1

                    # 5. Presenza di varianza (non costante)
                    if sstd is not None and sstd > 0:
                        score += 0.1

                    # 6. Range ragionevole per un prezzo (non troppo grande)
                    if smax is not None and smax < 1_000_000:
                        score += 0.05

            except Exception:
                pass

        return {
            "semantic_type": "price",
            "confidence": min(score, 1.0),
            "meta": meta,
        }
