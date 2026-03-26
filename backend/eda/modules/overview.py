import polars as pl
import plotly.graph_objects as go
import json


def _fig(fig: go.Figure) -> dict:
    return json.loads(fig.to_json())


def run(df: pl.DataFrame, df_full: pl.DataFrame, semantic_types: dict, groups: dict) -> dict:
    n_rows = len(df_full)
    n_cols = len(df_full.columns)
    n_cells = n_rows * n_cols
    memory_mb = round(df_full.estimated_size("mb"), 3)

    total_missing = sum(df_full[c].null_count() for c in df_full.columns)
    pct_missing_global = round(total_missing / n_cells * 100, 2) if n_cells > 0 else 0.0

    columns = []
    for col in df_full.columns:
        s = df_full[col]
        n_null = s.null_count()
        columns.append({
            "name": col,
            "dtype_original": str(s.dtype),
            "semantic_type": semantic_types.get(col, "unknown"),
            "n_unique": int(s.drop_nulls().n_unique()),
            "pct_missing": round(n_null / n_rows * 100, 2) if n_rows > 0 else 0.0,
            "role": _infer_role(col, semantic_types.get(col, "unknown")),
            "note": "",
        })

    groups_count = {k: len(v) for k, v in groups.items() if v}

    # Chart: tipi semantici
    type_labels = {
        "numeric_continuous": "Num. continuo",
        "numeric_discrete":   "Num. discreto",
        "categorical_nominal":"Categorico",
        "categorical_ordinal":"Categorico ord.",
        "boolean":            "Booleano",
        "datetime":           "Datetime",
        "text":               "Testo libero",
        "id":                 "ID / quasi-ID",
        "geographic":         "Geografico",
        "unknown":            "Sconosciuto",
    }
    gc_labels = [type_labels.get(k, k) for k, v in groups_count.items()]
    gc_values = list(groups_count.values())
    fig_types = go.Figure(go.Bar(
        x=gc_labels, y=gc_values,
        marker_color=["#FF4D00" if v == max(gc_values) else "#2B2B2B" for v in gc_values],
        text=gc_values, textposition="outside",
    ))
    fig_types.update_layout(
        title="Distribuzione tipi semantici",
        xaxis_title="Tipo", yaxis_title="N colonne",
        plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=12),
        margin=dict(t=50, b=60, l=50, r=20),
    )

    return {
        "n_rows": n_rows,
        "n_cols": n_cols,
        "n_cells": n_cells,
        "memory_mb": memory_mb,
        "pct_missing_global": pct_missing_global,
        "columns": columns,
        "groups_count": groups_count,
        "notes": _generate_notes(n_rows, n_cols, pct_missing_global, groups),
        "charts": {"types_distribution": _fig(fig_types)},
    }


def _infer_role(col: str, stype: str) -> str:
    if stype == "id":          return "chiave tecnica"
    if stype == "datetime":    return "temporale"
    if stype == "geographic":  return "spaziale"
    return "feature"


def _generate_notes(n_rows, n_cols, pct_missing, groups) -> list[str]:
    notes = []
    if pct_missing > 20:
        notes.append(f"Dataset con alta percentuale di valori mancanti ({pct_missing:.1f}%). Valutare la qualità delle sorgenti.")
    n_id = len(groups.get("id", []))
    if n_id > n_cols * 0.3:
        notes.append(f"Presenti {n_id} colonne ID o quasi-ID ({round(n_id/n_cols*100)}% del totale). Probabilmente da escludere.")
    n_cat = len(groups.get("categorical_nominal", [])) + len(groups.get("categorical_ordinal", []))
    if n_cat > n_cols * 0.5:
        notes.append(f"Dataset prevalentemente categorico ({n_cat}/{n_cols} colonne). Encoding necessario per la modellazione.")
    n_num = len(groups.get("numeric_continuous", [])) + len(groups.get("numeric_discrete", []))
    if n_num == 0:
        notes.append("Nessuna colonna numerica rilevata. Verificare numerici memorizzati come stringhe.")
    if n_rows > 500_000:
        notes.append(f"Dataset di grandi dimensioni ({n_rows:,} righe). Analisi eseguita su campione rappresentativo.")
    n_text = len(groups.get("text", []))
    if n_text > 0:
        notes.append(f"Presenti {n_text} colonne testuali. Richiedono pipeline NLP separata.")
    return notes

