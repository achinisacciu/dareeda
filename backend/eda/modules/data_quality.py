import json
from typing import Any

import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go
import polars as pl

MASKED_MISSING_TOKENS = (
    "",
    "na",
    "n/a",
    "null",
    "none",
    "nan",
    "nd",
    "n.d.",
    "-",
    "--",
    "?",
)

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _fig(fig: go.Figure) -> dict:
    return json.loads(fig.to_json())


def run(df: pl.DataFrame, df_full: pl.DataFrame, semantic_types: dict, groups: dict) -> dict:
    missing = _analyze_missing(df_full)
    duplicates = _analyze_duplicates(df_full)
    inconsistencies = _analyze_inconsistencies(df_full, semantic_types)
    text_cleaning = _analyze_text_cleaning(df_full)
    anomaly_overlap = _anomaly_overlap(df_full)

    standardized = _standardize_issues(
        missing=missing,
        duplicates=duplicates,
        inconsistencies=inconsistencies,
        text_cleaning=text_cleaning,
        anomaly_overlap=anomaly_overlap,
        n_rows=len(df_full),
        n_cols=len(df_full.columns),
    )

    # Manteniamo l'output attuale per non rompere la UI
    return {
        "missing": missing,
        "duplicates": duplicates,
        "inconsistencies": inconsistencies,
        "text_cleaning": text_cleaning,
        "anomaly_overlap": anomaly_overlap,
        # Output normalizzato per le prossime fasi (Pulizia / Transformation layer)
        "standardized_issues": standardized,
        "cleaning_summary": _build_cleaning_summary(
            standardized,
            n_rows=len(df_full),
            n_cols=len(df_full.columns),
        ),
    }


def _standardize_severity(sev: str) -> str:
    # Mappa severità esistente => low/medium/high
    if sev in ("none",):
        return "low"
    if sev in ("low",):
        return "low"
    if sev in ("moderate",):
        return "medium"
    if sev in ("high", "critical"):
        return "high"
    return "medium"


def _is_string_like_dtype(dtype: Any) -> bool:
    name = str(dtype).lower()
    return any(token in name for token in ("string", "str", "utf8", "categorical", "enum"))


def _format_scope(column: str | None) -> dict:
    if column:
        return {"type": "column", "label": f"Colonna `{column}`"}
    return {"type": "dataset", "label": "Intero dataset"}


def _make_issue_id(module: str, issue: str, column: str | None = None) -> str:
    return f"{module}:{issue}:{column or 'dataset'}"


def _stringify_example(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str) and value == "":
        return "(stringa vuota)"
    return str(value)


def _result_sentence_drop_column(column: str, n_cols: int) -> str:
    next_cols = max(n_cols - 1, 0)
    return (
        f"La colonna `{column}` verrà rimossa dal dataset usato nella nuova analisi. "
        f"Colonne stimate: {n_cols} -> {next_cols}."
    )


def _standardize_issues(
    *,
    missing: dict,
    duplicates: dict,
    inconsistencies: dict,
    text_cleaning: dict,
    anomaly_overlap: list,
    n_rows: int,
    n_cols: int,
) -> list[dict]:
    issues: list[dict] = []

    # Duplicati
    n_dup = duplicates.get("n_duplicate_rows") or 0
    pct_dup = duplicates.get("pct_duplicate_rows") or 0.0
    if n_dup > 0:
        sev = "medium"
        if pct_dup >= 5:
            sev = "high"
        issues.append({
            "id": _make_issue_id("duplicates", "duplicate_rows"),
            "module": "duplicates",
            "issue": "duplicate_rows",
            "title": "Righe duplicate esatte",
            "column": None,
            "scope": _format_scope(None),
            "severity": sev,
            "evidence": {"n_duplicate_rows": n_dup, "pct_duplicate_rows": pct_dup},
            "suggestion": "Deduplicare le righe esatte prima di rieseguire l'analisi.",
            "detection": {
                "summary": f"Rilevate {n_dup} righe duplicate esatte ({pct_dup}%).",
                "details": "Il confronto avviene sull'intera riga, usando tutte le colonne contemporaneamente.",
                "method": {
                    "type": "exact_row_match",
                    "label": "Confronto esatto riga per riga",
                    "uses_regex": False,
                },
            },
            "proposal": {
                "supported": True,
                "summary": "Mantieni solo la prima occorrenza di ogni riga identica.",
                "action_label": "Rimuovi righe duplicate esatte",
                "result": (
                    f"Saranno rimosse {n_dup} righe duplicate. "
                    f"Righe stimate: {n_rows} -> {max(n_rows - n_dup, 0)}."
                ),
                "impact": {
                    "rows_before": n_rows,
                    "rows_after": max(n_rows - n_dup, 0),
                    "rows_removed": n_dup,
                    "columns_before": n_cols,
                    "columns_after": n_cols,
                },
                "method": {
                    "label": "Deduplicazione esatta",
                    "uses_regex": False,
                    "notes": "Nessuna regex: vengono rimosse solo righe perfettamente identiche.",
                },
            },
            "preview": None,
            "action": {
                "type": "drop_duplicate_rows",
                "column": None,
                "params": {"mode": "exact"},
            },
        })

    # Inconsistenze / esclusione colonne
    near_constant_lookup = {
        c.get("variable"): c
        for c in (inconsistencies.get("near_constant") or [])
        if c.get("variable")
    }
    for c in inconsistencies.get("candidates_exclusion") or []:
        column = c.get("variable")
        reason = c.get("reason") or ""
        sev = "medium"
        if (
            "Missing" in reason
            or "eccessivo" in reason
            or "Costante" in reason
            or "Quasi" in reason
        ):
            sev = "high" if "Missing" in reason or "eccessivo" in reason else "medium"
        nc = near_constant_lookup.get(column) or {}
        details = [reason]
        if nc.get("dominant_share") is not None:
            details.append(f"Valore dominante: {nc.get('dominant_share')}%")
        if nc.get("unique_count") is not None:
            details.append(f"Valori unici osservati: {nc.get('unique_count')}")
        issues.append({
            "id": _make_issue_id("inconsistencies", "candidate_exclusion", column),
            "module": "inconsistencies",
            "issue": "candidate_exclusion",
            "title": "Colonna candidata all'esclusione",
            "column": column,
            "scope": _format_scope(column),
            "severity": sev,
            "evidence": {
                "reason": reason,
                "evidence": c.get("evidence"),
                "unique_count": nc.get("unique_count"),
                "dominant_share": nc.get("dominant_share"),
            },
            "suggestion": "Escludere la colonna dalla prossima analisi se il segnale informativo è troppo basso.",
            "detection": {
                "summary": f"La colonna `{column}` è stata segnalata come poco utile o problematica.",
                "details": ". ".join([d for d in details if d]),
                "method": {
                    "type": "column_profile",
                    "label": "Profilazione statistica della colonna",
                    "uses_regex": False,
                },
            },
            "proposal": {
                "supported": True,
                "summary": f"Escludi la colonna `{column}` dal dataset analizzato.",
                "action_label": f"Escludi colonna `{column}`",
                "result": _result_sentence_drop_column(column, n_cols),
                "impact": {
                    "rows_before": n_rows,
                    "rows_after": n_rows,
                    "columns_before": n_cols,
                    "columns_after": max(n_cols - 1, 0),
                    "columns_removed": 1,
                },
                "method": {
                    "label": "Esclusione di colonna",
                    "uses_regex": False,
                    "notes": "La colonna non viene trasformata: viene rimossa completamente dal dataset analizzato.",
                },
            },
            "preview": None,
            "action": {
                "type": "exclude_column",
                "column": column,
                "params": {"reason": reason},
            },
        })

    # Token missing mascherati
    for item in text_cleaning.get("masked_missing") or []:
        column = item.get("column")
        issues.append({
            "id": _make_issue_id("text_cleaning", "masked_missing_values", column),
            "module": "text_cleaning",
            "issue": "masked_missing_values",
            "title": "Valori mancanti mascherati",
            "column": column,
            "scope": _format_scope(column),
            "severity": _standardize_severity(item.get("severity") or "moderate"),
            "evidence": {
                "affected_count": item.get("count"),
                "affected_pct": item.get("pct"),
                "tokens": item.get("tokens"),
            },
            "suggestion": "Convertire questi token in `null` per rendere espliciti i missing.",
            "detection": {
                "summary": (
                    f"Nella colonna `{column}` sono stati trovati "
                    f"{item.get('count')} valori testuali che rappresentano missing."
                ),
                "details": f"Token rilevati: {', '.join(item.get('tokens_display') or [])}.",
                "method": {
                    "type": "exact_token_match",
                    "label": "Confronto esatto su testo normalizzato",
                    "uses_regex": False,
                },
            },
            "proposal": {
                "supported": True,
                "summary": "Sostituisci questi token con `null` senza alterare la struttura del dataset.",
                "action_label": f"Converti token missing in `null` su `{column}`",
                "result": (
                    f"Saranno convertite {item.get('count')} celle in `null`. "
                    f"Dimensioni dataset invariate: {n_rows} righe, {n_cols} colonne."
                ),
                "impact": {
                    "rows_before": n_rows,
                    "rows_after": n_rows,
                    "columns_before": n_cols,
                    "columns_after": n_cols,
                    "cells_modified": item.get("count"),
                },
                "method": {
                    "label": "Sostituzione per token esatti",
                    "uses_regex": False,
                    "notes": "Il matching usa trim + lowercase. Nessuna regex.",
                },
            },
            "preview": {
                "type": "before_after",
                "examples": [{"before": ex, "after": None} for ex in (item.get("examples") or [])],
            },
            "action": {
                "type": "replace_values",
                "column": column,
                "params": {
                    "match_mode": "exact_case_insensitive_trimmed",
                    "values": item.get("tokens") or [],
                    "replacement": None,
                },
            },
        })

    # Spazi iniziali/finali
    for item in text_cleaning.get("whitespace") or []:
        column = item.get("column")
        issues.append({
            "id": _make_issue_id("text_cleaning", "leading_trailing_whitespace", column),
            "module": "text_cleaning",
            "issue": "leading_trailing_whitespace",
            "title": "Spazi da normalizzare",
            "column": column,
            "scope": _format_scope(column),
            "severity": _standardize_severity(item.get("severity") or "low"),
            "evidence": {
                "affected_count": item.get("count"),
                "affected_pct": item.get("pct"),
            },
            "suggestion": "Ripulire gli spazi iniziali/finali per evitare duplicati logici o categorie incoerenti.",
            "detection": {
                "summary": (
                    f"La colonna `{column}` contiene "
                    f"{item.get('count')} celle con spazi iniziali o finali."
                ),
                "details": "Vengono rilevati solo spazi ai bordi della stringa; nessuna sostituzione interna.",
                "method": {
                    "type": "trim_whitespace",
                    "label": "Confronto valore originale vs valore trim",
                    "uses_regex": False,
                },
            },
            "proposal": {
                "supported": True,
                "summary": "Rimuovi gli spazi iniziali/finali lasciando invariato il contenuto centrale.",
                "action_label": f"Trim whitespace su `{column}`",
                "result": (
                    f"Verranno normalizzate {item.get('count')} celle. "
                    f"Dimensioni dataset invariate: {n_rows} righe, {n_cols} colonne."
                ),
                "impact": {
                    "rows_before": n_rows,
                    "rows_after": n_rows,
                    "columns_before": n_cols,
                    "columns_after": n_cols,
                    "cells_modified": item.get("count"),
                },
                "method": {
                    "label": "Trim stringhe",
                    "uses_regex": False,
                    "notes": "Nessuna regex: vengono rimossi solo gli spazi iniziali/finali.",
                },
            },
            "preview": {
                "type": "before_after",
                "examples": item.get("examples") or [],
            },
            "action": {
                "type": "trim_whitespace",
                "column": column,
                "params": {},
            },
        })

    # Anomalie overlap
    anomaly_rows = [item for item in (anomaly_overlap or []) if (item.get("count") or 0) > 0]
    if anomaly_rows:
        issues.append({
            "id": _make_issue_id("anomalies", "anomaly_row_patterns"),
            "module": "anomalies",
            "issue": "anomaly_row_patterns",
            "title": "Pattern di anomalie sulle righe",
            "column": None,
            "scope": _format_scope(None),
            "severity": "low",
            "evidence": {"patterns": anomaly_rows},
            "suggestion": "Rivedere i pattern anomali prima di scegliere una strategia di pulizia più aggressiva.",
            "detection": {
                "summary": "Sono presenti righe con combinazioni di missing e/o duplicazione.",
                "details": "; ".join(
                    f"{item.get('pattern')}: {item.get('count')} righe ({item.get('pct_rows')}%)"
                    for item in anomaly_rows
                ),
                "method": {
                    "type": "row_pattern_summary",
                    "label": "Sintesi pattern anomalie",
                    "uses_regex": False,
                },
            },
            "proposal": {
                "supported": False,
                "summary": (
                    "Nessuna azione automatica proposta: serve una scelta "
                    "consapevole sul significato di queste righe."
                ),
                "action_label": "Solo revisione",
                "result": "Questa rilevazione non modifica il dataset: è un promemoria di revisione.",
                "impact": {
                    "rows_before": n_rows,
                    "rows_after": n_rows,
                    "columns_before": n_cols,
                    "columns_after": n_cols,
                },
                "method": {
                    "label": "Review only",
                    "uses_regex": False,
                    "notes": "Segnalazione informativa senza trasformazione automatica.",
                },
            },
            "preview": None,
            "action": {
                "type": "review_only",
                "params": {},
            },
        })

    issues.sort(
        key=lambda item: (
            SEVERITY_RANK.get(item.get("severity", "medium"), 1),
            item.get("column") or "",
            item.get("title") or "",
        )
    )
    return issues


def _build_cleaning_summary(issues: list[dict], *, n_rows: int, n_cols: int) -> dict:
    actionable = [issue for issue in issues if (issue.get("proposal") or {}).get("supported")]
    review_only = [issue for issue in issues if not (issue.get("proposal") or {}).get("supported")]
    columns_impacted = sorted({issue.get("column") for issue in actionable if issue.get("column")})
    dataset_actions = [issue for issue in actionable if not issue.get("column")]

    return {
        "dataset_shape": {"rows": n_rows, "columns": n_cols},
        "issues_total": len(issues),
        "actionable_total": len(actionable),
        "review_only_total": len(review_only),
        "columns_impacted": columns_impacted,
        "dataset_level_actions": len(dataset_actions),
    }


# ── Missing ─────────────────────────────────────────────────────────────────


def _severity(pct: float) -> str:
    if pct == 0:
        return "none"
    if pct <= 5:
        return "low"
    if pct <= 20:
        return "moderate"
    if pct <= 40:
        return "high"
    return "critical"


def _analyze_missing(df: pl.DataFrame) -> dict:
    n_rows = len(df)
    n_cols = len(df.columns)
    n_cells = n_rows * n_cols

    per_col = []
    total_missing = 0
    rows_with_missing_mask = pl.Series([False] * n_rows)

    for col in df.columns:
        s = df[col]
        n_null = s.null_count()
        total_missing += n_null
        if n_null > 0:
            rows_with_missing_mask = rows_with_missing_mask | s.is_null()
        pct = round(n_null / n_rows * 100, 2) if n_rows > 0 else 0.0
        per_col.append({
            "variable": col,
            "missing_count": int(n_null),
            "missing_pct": pct,
            "severity": _severity(pct),
        })

    rows_with_missing = int(rows_with_missing_mask.sum())
    pct_rows = round(rows_with_missing / n_rows * 100, 2) if n_rows > 0 else 0.0
    pct_cells = round(total_missing / n_cells * 100, 2) if n_cells > 0 else 0.0

    # Missing per row distribution (usa campione per rapidità)
    sample = df.head(min(5000, n_rows))
    missing_per_row = pl.Series([
        sum(1 for col in sample.columns if sample[col][i] is None) for i in range(len(sample))
    ])

    # Chart: missing per colonna (solo colonne con missing > 0)
    cols_with_missing = [c for c in per_col if c["missing_count"] > 0]
    cols_with_missing.sort(key=lambda x: x["missing_pct"], reverse=True)

    colors_map = {
        "none": "#000000",
        "low": "#2B2B2B",
        "moderate": "#FF4D00",
        "high": "#FF4D00",
        "critical": "#B33600",
    }
    fig_missing = go.Figure(
        go.Bar(
            x=[c["variable"] for c in cols_with_missing],
            y=[c["missing_pct"] for c in cols_with_missing],
            marker_color=[colors_map[c["severity"]] for c in cols_with_missing],
            text=[f"{c['missing_pct']}%" for c in cols_with_missing],
            textposition="outside",
        )
    )
    fig_missing.update_layout(
        title="% Valori mancanti per variabile",
        xaxis_title="Variabile",
        yaxis_title="% Missing",
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=120, l=50, r=20),
        xaxis=dict(tickangle=-45),
    )

    # Heatmap missing su dataset completo.
    # Non campioniamo le righe: l'utente deve vedere i pattern reali di missing.
    hm_cols = (
        [c["variable"] for c in cols_with_missing[:30]] if cols_with_missing else df.columns[:30]
    )
    hm_matrix = (
        df.select([pl.col(col).is_null().cast(pl.Int8).alias(col) for col in hm_cols]).to_numpy()
        if hm_cols
        else np.empty((0, 0), dtype=np.int8)
    )
    fig_heatmap = go.Figure(
        go.Heatmap(
            z=hm_matrix.tolist(),
            x=hm_cols,
            colorscale=[[0, "#F5F5F5"], [1, "#FF4D00"]],
            showscale=True,
            colorbar=dict(title="Missing"),
        )
    )
    fig_heatmap.update_layout(
        title="Heatmap valori mancanti",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=10),
        margin=dict(t=50, b=100, l=120, r=20),
        xaxis=dict(tickangle=-45),
        yaxis=dict(showticklabels=False, title="Righe"),
    )

    pattern_charts = _missing_pattern_charts(df, cols_with_missing)

    # Commento AI
    critical = [c["variable"] for c in per_col if c["severity"] == "critical"]
    high_miss = [c["variable"] for c in per_col if c["severity"] == "high"]
    comment = _missing_comment(pct_cells, critical, high_miss)

    return {
        "global": {
            "n_rows": n_rows,
            "n_cols": n_cols,
            "n_cells": n_cells,
            "rows_with_missing": rows_with_missing,
            "pct_rows_with_missing": pct_rows,
            "total_missing_cells": int(total_missing),
            "pct_missing_cells": pct_cells,
            "mean_missing_per_row": round(float(missing_per_row.mean()), 2)
            if len(missing_per_row) > 0
            else 0.0,
            "median_missing_per_row": round(float(missing_per_row.median()), 2)
            if len(missing_per_row) > 0
            else 0.0,
        },
        "per_column": per_col,
        "charts": {
            "missing_bar": _fig(fig_missing) if cols_with_missing else None,
            "missing_heatmap": _fig(fig_heatmap) if cols_with_missing else None,
            "missing_cooccurrence": pattern_charts.get("missing_cooccurrence"),
            "missing_pattern_correlation": pattern_charts.get("missing_pattern_correlation"),
            "missing_dendrogram": pattern_charts.get("missing_dendrogram"),
        },
        "ai_comment": comment,
    }


def _missing_comment(pct_cells: float, critical: list, high: list) -> str:
    parts = []
    if pct_cells == 0:
        parts.append(
            "Il dataset non presenta valori mancanti. La qualità del dato è ottima sotto questo aspetto."
        )
    elif pct_cells < 5:
        parts.append(
            f"Il dataset presenta una bassa percentuale di valori mancanti ({pct_cells:.1f}%). "
            "L'impatto sulla modellazione è limitato."
        )
    elif pct_cells < 20:
        parts.append(
            f"Il dataset presenta una percentuale moderata di valori mancanti ({pct_cells:.1f}%). "
            "È consigliabile valutare strategie di imputazione."
        )
    else:
        parts.append(
            f"Il dataset presenta un'alta percentuale di valori mancanti ({pct_cells:.1f}%). "
            "È necessaria un'analisi approfondita prima della modellazione."
        )

    if critical:
        parts.append(
            f"Le colonne con severità critica (>40% missing) sono: {', '.join(critical[:5])}. "
            "Si consiglia di valutarne l'eliminazione o l'imputazione specifica."
        )
    if high:
        parts.append(
            f"Le colonne con alta presenza di missing (20-40%) sono: {', '.join(high[:5])}. "
            "Investigare possibili cause operative."
        )
    return " ".join(parts)


def _missing_pattern_charts(df: pl.DataFrame, cols_with_missing: list[dict]) -> dict:
    target_columns = [item["variable"] for item in cols_with_missing[:15]]
    if len(target_columns) < 2:
        return {
            "missing_cooccurrence": None,
            "missing_pattern_correlation": None,
            "missing_dendrogram": None,
        }

    matrix = df.select([
        pl.col(col).is_null().cast(pl.Int8).alias(col) for col in target_columns
    ]).to_numpy()
    if matrix.shape[0] < 2:
        return {
            "missing_cooccurrence": None,
            "missing_pattern_correlation": None,
            "missing_dendrogram": None,
        }

    absolute = matrix.T @ matrix
    max_abs = int(absolute.max()) if absolute.size else 0
    fig_abs = go.Figure(
        go.Heatmap(
            z=absolute.tolist(),
            x=target_columns,
            y=target_columns,
            colorscale=[[0, "#FFFFFF"], [0.5, "#59ADF7"], [1, "#E4002B"]],
            zmin=0,
            zmax=max_abs if max_abs > 0 else 1,
            text=absolute.tolist(),
            texttemplate="%{text}",
            hovertemplate="<b>%{x}</b> + <b>%{y}</b><br>Righe con missing congiunto: %{z}<extra></extra>",
            showscale=True,
        )
    )
    fig_abs.update_layout(
        title="Matrice co-occorrenza missing",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=10),
        margin=dict(t=70, b=120, l=120, r=20),
        xaxis=dict(tickangle=-45, title="<b>Colonne</b>"),
        yaxis=dict(title="<b>Colonne</b>"),
    )

    corr = np.corrcoef(matrix, rowvar=False)
    corr = np.nan_to_num(corr, nan=0.0)
    np.fill_diagonal(corr, 1.0)
    fig_corr = go.Figure(
        go.Heatmap(
            z=corr.tolist(),
            x=target_columns,
            y=target_columns,
            colorscale=[[0, "#0904AE"], [0.5, "#FFFFFF"], [1, "#E4002B"]],
            zmin=-1,
            zmax=1,
            zmid=0,
            text=[[f"{value:.2f}" for value in row] for row in corr.tolist()],
            texttemplate="%{text}",
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlazione pattern missing: %{z:.2f}<extra></extra>",
            showscale=True,
        )
    )
    fig_corr.update_layout(
        title="Correlazione pattern missing",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=10),
        margin=dict(t=70, b=120, l=120, r=20),
        xaxis=dict(tickangle=-45, title="<b>Colonne</b>"),
        yaxis=dict(title="<b>Colonne</b>"),
    )

    fig_dendrogram = None
    try:
        fig_dendrogram = ff.create_dendrogram(
            matrix.T,
            orientation="left",
            labels=target_columns,
            colorscale=["#59ADF7", "#0904AE", "#E4002B"],
        )
        fig_dendrogram.update_layout(
            title="Dendrogramma pattern missing",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=10),
            margin=dict(t=70, b=40, l=180, r=20),
            xaxis=dict(title="<b>Distanza</b>"),
            yaxis=dict(title="<b>Colonne</b>"),
            showlegend=False,
        )
    except Exception:
        fig_dendrogram = None

    return {
        "missing_cooccurrence": _fig(fig_abs),
        "missing_pattern_correlation": _fig(fig_corr),
        "missing_dendrogram": _fig(fig_dendrogram) if fig_dendrogram else None,
    }


# ── Duplicati ───────────────────────────────────────────────────────────────


def _analyze_duplicates(df: pl.DataFrame) -> dict:
    n_rows = len(df)
    n_dup = int(df.is_duplicated().sum())
    n_unique_rows = n_rows - n_dup
    pct_dup = round(n_dup / n_rows * 100, 2) if n_rows > 0 else 0.0

    if pct_dup == 0:
        comment = "Nessun duplicato esatto rilevato. Il dataset è privo di righe identiche."
    elif pct_dup < 1:
        comment = (
            f"Presenza trascurabile di duplicati ({pct_dup:.2f}%). Impatto sulla qualità minimo."
        )
    elif pct_dup < 5:
        comment = (
            f"Presenza lieve di duplicati ({pct_dup:.1f}%). "
            "Si consiglia di investigare la causa prima di procedere."
        )
    else:
        comment = (
            f"Presenza significativa di duplicati ({pct_dup:.1f}%). "
            "La rimozione è fortemente consigliata prima della modellazione."
        )

    return {
        "n_duplicate_rows": n_dup,
        "pct_duplicate_rows": pct_dup,
        "n_unique_rows": n_unique_rows,
        "ai_comment": comment,
    }


# ── Inconsistenze ───────────────────────────────────────────────────────────


def _analyze_inconsistencies(df: pl.DataFrame, semantic_types: dict) -> dict:
    near_constant = []
    candidates_exclusion = []

    for col in df.columns:
        s = df[col].drop_nulls()
        if len(s) == 0:
            continue
        n_unq = s.n_unique()
        dominant_share = (
            round(float(s.value_counts(sort=True).head(1)["count"][0]) / len(s) * 100, 2)
            if n_unq > 0
            else 100.0
        )
        flag = None
        if n_unq == 1:
            flag = "costante"
            candidates_exclusion.append({
                "variable": col,
                "reason": "Costante (zero varianza)",
                "evidence": f"unico valore: {s[0]}",
            })
        elif dominant_share >= 99 and n_unq <= 2:
            flag = "quasi-costante"
            candidates_exclusion.append({
                "variable": col,
                "reason": "Quasi-costante (≥99% stesso valore)",
                "evidence": f"{dominant_share}% valore dominante",
            })

        if flag:
            near_constant.append({
                "variable": col,
                "unique_count": n_unq,
                "dominant_share": dominant_share,
                "flag": flag,
            })

    # Colonne con troppi missing
    n_rows = len(df)
    for col in df.columns:
        pct_m = df[col].null_count() / n_rows * 100 if n_rows > 0 else 0
        if pct_m > 60:
            already = any(c["variable"] == col for c in candidates_exclusion)
            if not already:
                candidates_exclusion.append({
                    "variable": col,
                    "reason": "Missing eccessivo (>60%)",
                    "evidence": f"{pct_m:.1f}% valori mancanti",
                })

    return {
        "near_constant": near_constant,
        "candidates_exclusion": candidates_exclusion,
    }


def _analyze_text_cleaning(df: pl.DataFrame) -> dict:
    masked_missing = []
    whitespace = []
    n_rows = len(df)

    for col in df.columns:
        series = df[col]
        if not _is_string_like_dtype(series.dtype):
            continue

        s = series.cast(pl.String, strict=False)
        normalized = s.str.strip_chars().str.to_lowercase()
        missing_mask = s.is_not_null() & normalized.is_in(list(MASKED_MISSING_TOKENS))
        missing_count = int(missing_mask.sum())

        if missing_count > 0:
            normalized_tokens = normalized.filter(missing_mask).unique().drop_nulls().to_list()
            normalized_tokens = sorted(str(tok) for tok in normalized_tokens)
            raw_examples = s.filter(missing_mask).unique().head(5).to_list()
            pct = round(missing_count / n_rows * 100, 2) if n_rows > 0 else 0.0
            masked_missing.append({
                "column": col,
                "count": missing_count,
                "pct": pct,
                "severity": _severity(pct),
                "tokens": normalized_tokens,
                "tokens_display": [_stringify_example(tok) for tok in normalized_tokens],
                "examples": [_stringify_example(ex) for ex in raw_examples],
            })

        trimmed = s.str.strip_chars()
        trimmed_norm = trimmed.str.to_lowercase()
        whitespace_mask = (
            s.is_not_null() & (s != trimmed) & ~trimmed_norm.is_in(list(MASKED_MISSING_TOKENS))
        )
        whitespace_count = int(whitespace_mask.sum())

        if whitespace_count > 0:
            before_vals = s.filter(whitespace_mask).head(5).to_list()
            after_vals = trimmed.filter(whitespace_mask).head(5).to_list()
            pct = round(whitespace_count / n_rows * 100, 2) if n_rows > 0 else 0.0
            whitespace.append({
                "column": col,
                "count": whitespace_count,
                "pct": pct,
                "severity": _severity(pct),
                "examples": [
                    {"before": _stringify_example(before), "after": _stringify_example(after)}
                    for before, after in zip(before_vals, after_vals, strict=False)
                ],
            })

    return {
        "masked_missing": masked_missing,
        "whitespace": whitespace,
    }


# ── Overlap anomalie ─────────────────────────────────────────────────────────


def _anomaly_overlap(df: pl.DataFrame) -> dict:
    n_rows = len(df)
    dup_mask = df.is_duplicated()
    miss_mask = pl.Series([
        any(df[col][i] is None for col in df.columns) for i in range(min(n_rows, 10_000))
    ])

    # Solo sui primi 10k per performance
    n_sample = min(n_rows, 10_000)
    dup_s = dup_mask[:n_sample]
    miss_s = miss_mask

    def cnt(mask) -> int:
        return int(mask.sum())

    def pct(n) -> float:
        return round(n / n_sample * 100, 2)

    n_miss_only = cnt(miss_s & ~dup_s)
    n_dup_only = cnt(dup_s & ~miss_s)
    n_both = cnt(miss_s & dup_s)
    n_none = n_sample - n_miss_only - n_dup_only - n_both

    return [
        {"pattern": "Solo missing", "count": n_miss_only, "pct_rows": pct(n_miss_only)},
        {"pattern": "Solo duplicato", "count": n_dup_only, "pct_rows": pct(n_dup_only)},
        {"pattern": "Missing + Duplicato", "count": n_both, "pct_rows": pct(n_both)},
        {"pattern": "Nessuna anomalia", "count": n_none, "pct_rows": pct(n_none)},
    ]
