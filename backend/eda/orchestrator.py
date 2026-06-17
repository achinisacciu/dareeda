"""
eda/orchestrator.py

Orchestratore stateless: riceve df_full + context, esegue tutti i moduli EDA
e restituisce un dizionario strutturato con:

  results = {
      "status":               "completed",
      "meta":                 { ... },          # info sul dataset e sul run
      "feature_engineering":  { ... },          # feature aggiunte + cleaning
      "overview":             { ... },
      "data_quality":         { ... },
      "univariate":           { ... },
      "bivariate":            { ... },
      "multivariate":         { ... },
      "timeseries":           { ... },
      "ml_exploratory":       { ... },
      "inference":            { ... },
      "insights":             { ... },
  }
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import polars as pl
from core.sampling import maybe_sample
from core.semantic_typer import group_by_semantic, type_dataframe
from eda.modules import (
    bivariate,
    data_quality,
    inference,
    insights,
    ml_exploratory,
    multivariate,
    overview,
    timeseries,
    univariate,
)

logger = logging.getLogger(__name__)

AcceptedFeature = dict[str, Any]
CleaningAction = dict[str, Any]
ModuleResult = dict[str, Any]
SemanticTypes = dict[str, str]
SemanticGroups = dict[str, list[str]]

MODULES: list[tuple[str, str, Any]] = [
    ("overview", "Panoramica dataset", overview.run),
    ("data_quality", "Qualità del dato", data_quality.run),
    ("univariate", "Analisi univariata", univariate.run),
    ("bivariate", "Analisi bivariata", bivariate.run),
    ("multivariate", "Analisi multivariata", multivariate.run),
    ("timeseries", "Serie temporali", timeseries.run),
    ("ml_exploratory", "ML esplorativo", ml_exploratory.run),
    ("inference", "Inferenza statistica", inference.run),
    ("insights", "Insights finali", insights.run),
]


# ─────────────────────────────────────────────────────────────────────────────
# Feature Engineering
# ─────────────────────────────────────────────────────────────────────────────


def _compute_accepted_features(
    df: pl.DataFrame,
    accepted: list[AcceptedFeature],
) -> tuple[pl.DataFrame, list[str]]:
    """
    Applica le feature accettate dall'utente al DataFrame.
    Restituisce il DataFrame aggiornato e la lista dei nomi delle colonne aggiunte.
    """
    added_cols = []

    for feature in accepted:
        name = feature.get("name")
        formula = feature.get("formula", "")
        sources = feature.get("source_columns", [])

        if not name or not formula:
            logger.debug(
                "Feature engineering saltata: nome o formula mancanti. Feature=%s, sources=%s",
                name,
                sources,
            )
            continue

        if not all(col in df.columns for col in sources):
            logger.debug(
                "Feature engineering saltata: colonne source non presenti nel DataFrame. "
                "Feature=%s, sources=%s, columns=%s",
                name,
                sources,
                list(df.columns),
            )
            continue

        try:
            feat_type = feature.get("type", "")

            if feat_type == "revenue" and len(sources) == 2:
                left = df[sources[0]].cast(pl.Float64, strict=False)
                right = df[sources[1]].cast(pl.Float64, strict=False)
                df = df.with_columns((left * right).alias(name))
                added_cols.append(name)

            elif feat_type == "margin" and len(sources) == 2:
                left = df[sources[0]].cast(pl.Float64, strict=False)
                right = df[sources[1]].cast(pl.Float64, strict=False)
                df = df.with_columns((left - right).alias(name))
                added_cols.append(name)

            elif feat_type == "margin_pct" and len(sources) == 2:
                sell = df[sources[0]].cast(pl.Float64, strict=False)
                cost = df[sources[1]].cast(pl.Float64, strict=False)
                df = df.with_columns((((sell - cost) / sell.replace(0, None)) * 100).alias(name))
                added_cols.append(name)

            elif feat_type == "ratio" and len(sources) == 2:
                num = df[sources[0]].cast(pl.Float64, strict=False)
                den = df[sources[1]].cast(pl.Float64, strict=False).replace(0, None)
                df = df.with_columns((num / den).alias(name))
                added_cols.append(name)

            elif feat_type == "discount" and len(sources) == 2:
                price = df[sources[0]].cast(pl.Float64, strict=False)
                discount = df[sources[1]].cast(pl.Float64, strict=False)
                d_max = discount.drop_nulls().max()
                if d_max is not None and d_max <= 1.0:
                    df = df.with_columns((price * (1 - discount)).alias(name))
                else:
                    df = df.with_columns((price * (1 - discount / 100)).alias(name))
                added_cols.append(name)

            elif feat_type == "derived_feature" and isinstance(formula, str):
                import re

                f = formula.strip()
                m = re.match(r"^(year|month)\((.+)\)$", f, flags=re.IGNORECASE)
                if m:
                    fn = m.group(1).lower()
                    src_col = m.group(2).strip()
                    if src_col in df.columns:
                        s = df[src_col]
                        if s.dtype not in (pl.Date, pl.Datetime):
                            s = s.cast(pl.String).str.to_datetime(strict=False)
                        s_dt = s.cast(pl.Datetime, strict=False)
                        col = s_dt.dt.year() if fn == "year" else s_dt.dt.month()
                        df = df.with_columns(col.alias(name))
                        added_cols.append(name)

        except Exception:
            logger.exception(
                "Feature engineering fallita. Feature=%s, type=%s, sources=%s",
                name,
                feat_type,
                sources,
            )
            continue

    return df, added_cols


# ─────────────────────────────────────────────────────────────────────────────
# Data Cleaning
# ─────────────────────────────────────────────────────────────────────────────


def _is_string_like_dtype(dtype: Any) -> bool:
    name = str(dtype).lower()
    return any(token in name for token in ("string", "str", "utf8", "categorical", "enum"))


def _apply_single_action(frame: pl.DataFrame, act: CleaningAction | None) -> pl.DataFrame:
    """Applica una singola azione di pulizia al DataFrame."""
    act_type = (act or {}).get("type")
    params = (act or {}).get("params") or {}
    col = (act or {}).get("column")

    if act_type == "exclude_column" and col and col in frame.columns:
        return frame.drop(col)

    if act_type == "drop_duplicate_rows":
        return frame.unique(maintain_order=True)

    if (
        act_type == "replace_values"
        and col
        and col in frame.columns
        and _is_string_like_dtype(frame.schema.get(col))
    ):
        match_mode = params.get("match_mode") or "exact"
        values = params.get("values") or []
        normalized = [str(v).strip().lower() for v in values if v is not None]
        if not normalized:
            return frame
        source = pl.col(col).cast(pl.String, strict=False)
        if match_mode == "exact_case_insensitive_trimmed":
            match_expr = source.str.strip_chars().str.to_lowercase().is_in(normalized)
        else:
            match_expr = source.is_in([str(v) for v in values if v is not None])
        return frame.with_columns(
            pl.when(match_expr).then(pl.lit(None, dtype=pl.String)).otherwise(source).alias(col)
        )

    if (
        act_type == "trim_whitespace"
        and col
        and col in frame.columns
        and _is_string_like_dtype(frame.schema.get(col))
    ):
        source = pl.col(col).cast(pl.String, strict=False)
        return frame.with_columns(
            pl
            .when(pl.col(col).is_null())
            .then(pl.lit(None, dtype=pl.String))
            .otherwise(source.str.strip_chars())
            .alias(col)
        )

    return frame


# ─────────────────────────────────────────────────────────────────────────────
# Orchestratore principale
# ─────────────────────────────────────────────────────────────────────────────


def run_analysis_stateless(
    df_full: pl.DataFrame,
    filename: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Esegue l'intera pipeline EDA in modo stateless.

    Parametri
    ---------
    df_full  : DataFrame Polars completo (già caricato in memoria)
    filename : Nome del file originale (usato come label nei risultati)
    context  : Dizionario di configurazione dal frontend:
                 - target, problem_type
                 - semantic_overrides
                 - selected_features
                 - accepted_features
                 - cleaning_actions

    Restituisce
    -----------
    dict strutturato con meta, feature_engineering e tutti i moduli EDA.
    """
    start_time = datetime.now(UTC)
    context = context or {}

    # ── 1. Campionamento ──────────────────────────────────────────────────────
    df, sampled, sample_n = maybe_sample(df_full)

    # ── 2. Feature Engineering ────────────────────────────────────────────────
    accepted_features = []
    for item in context.get("accepted_features", []):
        if isinstance(item, dict):
            accepted_features.append(item)
        elif isinstance(item, str):
            accepted_features.append({
                "name": item,
                "type": "unknown",
                "source_columns": [],
                "formula": "",
                "status": "accepted",
            })

    added_cols = []
    if accepted_features:
        df, added_cols = _compute_accepted_features(df, accepted_features)
        df_full, _ = _compute_accepted_features(df_full, accepted_features)

    # ── 3. Cleaning ───────────────────────────────────────────────────────────
    pre_clean_rows = len(df_full)
    pre_clean_cols = len(df_full.columns)

    cleaning_actions = context.get("cleaning_actions") or []
    for act in cleaning_actions:
        df = _apply_single_action(df, act)
        df_full = _apply_single_action(df_full, act)

    cleaning_summary = {
        "actions": cleaning_actions,
        "before_rows": pre_clean_rows,
        "after_rows": len(df_full),
        "before_cols": pre_clean_cols,
        "after_cols": len(df_full.columns),
        "rows_removed": pre_clean_rows - len(df_full),
        "cols_removed": pre_clean_cols - len(df_full.columns),
    }

    # ── 4. Semantic typing ────────────────────────────────────────────────────
    semantic_types = type_dataframe(df)
    groups = group_by_semantic(semantic_types)

    # ── 5. Struttura risultato ────────────────────────────────────────────────
    results = {
        "status": "completed",
        # Metadati del run e del dataset
        "meta": {
            "dataset_filename": filename,
            "generated_at": datetime.now(UTC).isoformat(),
            "target": context.get("target"),
            "problem_type": context.get("problem_type"),
            "n_rows_full": len(df_full),
            "n_cols": len(df_full.columns),
            "sampled": sampled,
            "sample_n": sample_n,
            "semantic_types": semantic_types,
            "runtime_seconds": None,  # aggiornato alla fine
        },
        # Feature engineering e cleaning applicati
        "feature_engineering": {
            "accepted_features": accepted_features,
            "derived_columns": added_cols,
            "cleaning": cleaning_summary,
        },
    }

    # ── 6. Esecuzione moduli EDA ──────────────────────────────────────────────
    for key, _label, fn in MODULES:
        try:
            if key in ("ml_exploratory", "multivariate"):
                results[key] = fn(
                    df=df,
                    df_full=df_full,
                    semantic_types=semantic_types,
                    groups=groups,
                    context=context,
                )
            else:
                results[key] = fn(
                    df=df,
                    df_full=df_full,
                    semantic_types=semantic_types,
                    groups=groups,
                )
        except Exception as e:
            logger.exception("Modulo EDA fallito: %s", key)
            results[key] = {"error": str(e), "skipped": True}

    # ── 7. Runtime finale ─────────────────────────────────────────────────────
    runtime = max((datetime.now(UTC) - start_time).total_seconds(), 0.0)
    results["meta"]["runtime_seconds"] = runtime

    return results
