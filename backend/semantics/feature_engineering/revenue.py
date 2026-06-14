"""
Revenue Rule — crea misure di ricavo combinando colonne price × quantity.
Logica intelligente: abbina le colonne per nome/contesto invece di fare
il prodotto cartesiano di tutti i price × tutti i quantity.
"""


# Keyword che indicano un prezzo "unitario" (preferiti per il calcolo ricavo)
UNIT_PRICE_HINTS = [
    "unit", "single", "each", "per", "unitario", "unitaria",
    "list", "base", "standard", "regular",
]

# Keyword che indicano un prezzo "totale" (da evitare nel calcolo ricavo)
TOTAL_PRICE_HINTS = [
    "total", "totale", "sum", "gross", "net", "subtotal",
    "revenue", "ricavo", "amount", "importo",
]


def _is_unit_price(col_name: str) -> bool:
    col_lower = col_name.lower()
    has_unit_hint = any(h in col_lower for h in UNIT_PRICE_HINTS)
    has_total_hint = any(h in col_lower for h in TOTAL_PRICE_HINTS)
    return has_unit_hint and not has_total_hint


def _columns_are_related(price_col: str, qty_col: str) -> float:
    """
    Restituisce un bonus di affinità semantica tra una colonna price e una qty.
    Cerca prefissi/suffissi comuni (es. 'product_price' e 'product_qty').
    """
    p = price_col.lower().replace("price", "").replace("prezzo", "").replace("costo", "").strip("_")
    q = qty_col.lower().replace("qty", "").replace("quantity", "").replace("quantita", "").strip("_")

    if not p or not q:
        return 0.0

    # Prefisso comune
    if p and q and (p.startswith(q) or q.startswith(p)):
        return 0.1

    # Stesso prefisso di almeno 3 caratteri
    common = 0
    for a, b in zip(p, q, strict=False):
        if a == b:
            common += 1
        else:
            break
    if common >= 3:
        return 0.08

    return 0.0


class RevenueRule:
    def apply(self, df, semantics):
        price_cols = [c for c, v in semantics.items() if v["semantic_type"] == "price"]
        qty_cols   = [c for c, v in semantics.items() if v["semantic_type"] == "quantity"]

        if not price_cols or not qty_cols:
            return []

        features = []

        # Preferisci prezzi unitari; se non ce ne sono, usa tutti
        unit_prices = [c for c in price_cols if _is_unit_price(c)]
        candidate_prices = unit_prices if unit_prices else price_cols

        # Evita di generare troppe combinazioni (max 6 misure)
        MAX_FEATURES = 6
        generated = 0

        for p in candidate_prices:
            for q in qty_cols:
                if generated >= MAX_FEATURES:
                    break

                p_conf = semantics[p]["confidence"]
                q_conf = semantics[q]["confidence"]
                affinity = _columns_are_related(p, q)

                # Confidenza combinata: media pesata + bonus affinità
                combined_conf = round(
                    (p_conf * 0.5 + q_conf * 0.5) + affinity,
                    3
                )

                feature_name = f"revenue_{p}_x_{q}" if len(price_cols) > 1 or len(qty_cols) > 1 else "revenue"

                features.append({
                    "name": feature_name,
                    "formula": f"{p} * {q}",
                    "description": f"Ricavo calcolato come {p} × {q}",
                    "type": "revenue",
                    "source_columns": [p, q],
                    "confidence": min(combined_conf, 1.0),
                    "status": "pending",
                })
                generated += 1

        return features
