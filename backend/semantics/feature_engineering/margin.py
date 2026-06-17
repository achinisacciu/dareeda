"""
Margin Rule — crea misure di margine e sconto.
Rileva coppie (prezzo_vendita, costo) e (prezzo, sconto) nel dataset.
"""

# Keyword che indicano prezzo di vendita
SELLING_PRICE_HINTS = [
    "selling",
    "sale",
    "sell",
    "vendita",
    "list",
    "retail",
    "price",
    "prezzo",
    "prix",
    "precio",
]

# Keyword che indicano costo/costo d'acquisto
COST_HINTS = [
    "cost",
    "costo",
    "purchase",
    "acquisto",
    "buying",
    "wholesale",
    "ingrosso",
    "supplier",
    "fornitore",
]

# Keyword che indicano sconto
DISCOUNT_HINTS = [
    "discount",
    "sconto",
    "rebate",
    "remise",
    "descuento",
    "rabatt",
    "reduction",
    "promo",
]


def _best_match(col_name: str, hints: list) -> float:
    """Restituisce uno score 0-1 di quanto il nome colonna corrisponde ai hint."""
    col_lower = col_name.lower()
    matches = sum(1 for h in hints if h in col_lower)
    return min(matches / 2, 1.0)


class MarginRule:
    def apply(self, df, semantics):
        price_cols = [c for c, v in semantics.items() if v["semantic_type"] == "price"]

        if len(price_cols) < 2:
            return []

        features = []
        used = set()

        # Cerca coppie (prezzo_vendita, costo) per il margine
        for p1 in price_cols:
            for p2 in price_cols:
                if p1 == p2:
                    continue
                pair = tuple(sorted([p1, p2]))
                if pair in used:
                    continue

                p1_sell_score = _best_match(p1, SELLING_PRICE_HINTS)
                p1_cost_score = _best_match(p1, COST_HINTS)
                p2_sell_score = _best_match(p2, SELLING_PRICE_HINTS)
                p2_cost_score = _best_match(p2, COST_HINTS)

                # Determina chi è prezzo vendita e chi è costo
                if p1_sell_score > p1_cost_score and p2_cost_score > p2_sell_score:
                    sell_col, cost_col = p1, p2
                elif p2_sell_score > p2_cost_score and p1_cost_score > p1_sell_score:
                    sell_col, cost_col = p2, p1
                else:
                    continue  # Ambiguo, non generare

                used.add(pair)
                conf = round(
                    (semantics[sell_col]["confidence"] + semantics[cost_col]["confidence"]) / 2, 3
                )

                # Margine assoluto
                features.append({
                    "name": f"margin_{sell_col}",
                    "formula": f"{sell_col} - {cost_col}",
                    "description": f"Margine assoluto: {sell_col} - {cost_col}",
                    "type": "margin",
                    "source_columns": [sell_col, cost_col],
                    "confidence": conf,
                    "status": "pending",
                })

                # Margine percentuale
                features.append({
                    "name": f"margin_pct_{sell_col}",
                    "formula": f"({sell_col} - {cost_col}) / NULLIF({sell_col}, 0) * 100",
                    "description": "Margine % su prezzo di vendita",
                    "type": "margin_pct",
                    "source_columns": [sell_col, cost_col],
                    "confidence": round(conf * 0.95, 3),
                    "status": "pending",
                })

        # Cerca coppie (prezzo, sconto) per il prezzo netto
        discount_cols = [
            c
            for c, v in semantics.items()
            if v["semantic_type"] in ("price", "percentage") and _best_match(c, DISCOUNT_HINTS) > 0
        ]

        for p in price_cols:
            for d in discount_cols:
                if p == d:
                    continue
                pair = tuple(sorted([p, d]))
                if pair in used:
                    continue
                used.add(pair)

                conf = round((semantics[p]["confidence"] + semantics[d]["confidence"]) / 2 * 0.9, 3)
                features.append({
                    "name": f"net_price_{p}",
                    "formula": f"{p} * (1 - {d})"
                    if semantics[d].get("meta", {}).get("scale") == "0-1"
                    else f"{p} * (1 - {d} / 100)",
                    "description": f"Prezzo netto dopo sconto {d}",
                    "type": "discount",
                    "source_columns": [p, d],
                    "confidence": conf,
                    "status": "pending",
                })

        return features
