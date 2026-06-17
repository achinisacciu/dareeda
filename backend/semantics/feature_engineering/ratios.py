"""
Ratio Rule — crea rapporti tra colonne quantity semanticamente sensati.
Non fa combinazioni a caso: abbina colonne che hanno una relazione logica
(es. venduto/disponibile, ordini/clienti).
"""

# Coppie semanticamente sensate: (keyword_numeratore, keyword_denominatore, nome_misura)
MEANINGFUL_PAIRS = [
    # Vendite / Stock
    (
        ["sold", "venduto", "vendite", "sales"],
        ["stock", "available", "disponibile", "inventory"],
        "sell_through_rate",
    ),
    # Ordini / Clienti
    (["orders", "ordini"], ["customers", "clienti", "users", "utenti"], "orders_per_customer"),
    # Resi / Vendite
    (["returns", "resi", "refunds"], ["sold", "venduto", "sales", "vendite"], "return_rate"),
    # Completati / Totali
    (["completed", "completati", "done"], ["total", "totale", "all", "tutti"], "completion_rate"),
    # Attivi / Totali
    (["active", "attivi"], ["total", "totale"], "activation_rate"),
]

MAX_FALLBACK_RATIOS = 3


def _col_matches(col_name: str, keywords: list) -> bool:
    col_lower = col_name.lower()
    return any(kw in col_lower for kw in keywords)


class RatioRule:
    def apply(self, df, semantics):
        qty_cols = [c for c, v in semantics.items() if v["semantic_type"] == "quantity"]

        if len(qty_cols) < 2:
            return []

        features = []
        used_pairs = set()

        # Fase 1: cerca coppie semanticamente sensate
        for num_kws, den_kws, ratio_name in MEANINGFUL_PAIRS:
            numerators = [c for c in qty_cols if _col_matches(c, num_kws)]
            denominators = [c for c in qty_cols if _col_matches(c, den_kws)]

            for num in numerators:
                for den in denominators:
                    if num == den:
                        continue
                    pair = tuple(sorted([num, den]))
                    if pair in used_pairs:
                        continue

                    used_pairs.add(pair)
                    num_conf = semantics[num]["confidence"]
                    den_conf = semantics[den]["confidence"]

                    features.append({
                        "name": ratio_name
                        if ratio_name not in [f["name"] for f in features]
                        else f"{ratio_name}_{num}",
                        "formula": f"{num} / NULLIF({den}, 0)",
                        "description": f"Rapporto tra {num} e {den}",
                        "type": "ratio",
                        "source_columns": [num, den],
                        "confidence": round((num_conf + den_conf) / 2, 3),
                        "status": "pending",
                    })

        # Fase 2: fallback — combina i primi qty ordinati per confidenza
        # solo se non abbiamo trovato nulla nella fase 1
        if not features:
            sorted_qty = sorted(qty_cols, key=lambda c: semantics[c]["confidence"], reverse=True)
            import itertools

            count = 0
            for q1, q2 in itertools.combinations(sorted_qty, 2):
                if count >= MAX_FALLBACK_RATIOS:
                    break
                pair = tuple(sorted([q1, q2]))
                if pair not in used_pairs:
                    used_pairs.add(pair)
                    features.append({
                        "name": f"ratio_{q1}_per_{q2}",
                        "formula": f"{q1} / NULLIF({q2}, 0)",
                        "description": f"Rapporto generico tra {q1} e {q2}",
                        "type": "ratio",
                        "source_columns": [q1, q2],
                        "confidence": round(
                            (semantics[q1]["confidence"] + semantics[q2]["confidence"]) / 2 * 0.7, 3
                        ),
                        "status": "pending",
                    })
                    count += 1

        return features
