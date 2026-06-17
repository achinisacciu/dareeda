import polars as pl
from semantics.base import BaseDetector
from semantics.keywords import QUANTITY_KEYWORDS


class QuantityDetector(BaseDetector):
    name = "quantity"

    INTEGER_DTYPES = (
        pl.Int8,
        pl.Int16,
        pl.Int32,
        pl.Int64,
        pl.UInt8,
        pl.UInt16,
        pl.UInt32,
        pl.UInt64,
    )
    NUMERIC_DTYPES = INTEGER_DTYPES + (pl.Float32, pl.Float64)

    def detect(self, df, col):
        score = 0.0
        col_lower = col.lower()
        meta = {}

        # 1. Match keyword nel nome colonna
        for kw in QUANTITY_KEYWORDS:
            if col_lower == kw:
                score += 0.6
                break
            if kw in col_lower:
                score += 0.4
                break

        series = df[col]

        # 2. Tipo numerico (Polars-style)
        if series.dtype in self.NUMERIC_DTYPES:
            score += 0.15

            # Bonus per interi (quantità sono quasi sempre interi)
            if series.dtype in self.INTEGER_DTYPES:
                score += 0.1

            try:
                non_null = series.drop_nulls()

                if len(non_null) > 0:
                    smin = non_null.min()
                    smax = non_null.max()
                    n_unique = non_null.n_unique()

                    meta["min"] = smin
                    meta["max"] = smax
                    meta["n_unique"] = n_unique

                    # 3. Valori non negativi
                    if smin is not None and smin >= 0:
                        score += 0.15

                    # 4. Non binario (non è un flag 0/1)
                    if n_unique > 2:
                        score += 0.1

                    # 5. Float con valori interi (es. 1.0, 2.0, 3.0)
                    if series.dtype in (pl.Float32, pl.Float64):
                        n_integer_like = (non_null == non_null.cast(pl.Int64)).sum()
                        if n_integer_like / len(non_null) > 0.95:
                            score += 0.1
                            meta["integer_like"] = True

            except Exception:
                pass

        return {
            "semantic_type": "quantity",
            "confidence": min(score, 1.0),
            "meta": meta,
        }
