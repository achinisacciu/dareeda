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
import re
from datetime import UTC, datetime
from typing import Any

import polars as pl
from core.models import AcceptedFeature, CleaningAction, EdaContext
from core.sampling import maybe_sample
from core.semantic_typer import analyze_datetime_features, group_by_semantic, type_dataframe
from eda.modules import (
    bivariate,
    data_quality,
    inference,
    ml_exploratory,
    multivariate,
    overview,
    timeseries,
    univariate,
)

logger = logging.getLogger(__name__)

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
]


# ─────────────────────────────────────────────────────────────────────────────
# Feature Engineering
# ─────────────────────────────────────────────────────────────────────────────


def _compute_accepted_features(
    df: pl.DataFrame,
    accepted: list[AcceptedFeature],
) -> tuple[pl.DataFrame, list[str], list[dict]]:
    """
    Applica le feature accettate dall'utente al DataFrame.
    Restituisce il DataFrame aggiornato, la lista dei nomi delle colonne aggiunte, e una lista di warning.
    """
    added_cols = []
    warnings = []

    for feature in accepted:
        name = feature.name
        formula = feature.formula or ""
        sources = feature.source_columns
        feat_type = feature.type

        if not name or not formula:
            warnings.append({"feature": name or "unknown", "reason": "Nome o formula mancanti."})
            logger.debug(
                "Feature engineering saltata: nome o formula mancanti. Feature=%s, sources=%s",
                name,
                sources,
            )
            continue

        if not all(col in df.columns for col in sources):
            warnings.append({"feature": name, "reason": "Colonne source non presenti nel DataFrame."})
            logger.debug(
                "Feature engineering saltata: colonne source non presenti nel DataFrame. "
                "Feature=%s, sources=%s, columns=%s",
                name,
                sources,
                list(df.columns),
            )
            continue

        try:
            feat_type = feature.type

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
                sell_no_zero = pl.when(sell == 0).then(None).otherwise(sell)
                df = df.with_columns((((sell - cost) / sell_no_zero) * 100).alias(name))
                added_cols.append(name)

            elif feat_type == "ratio" and len(sources) == 2:
                num = df[sources[0]].cast(pl.Float64, strict=False)
                den = df[sources[1]].cast(pl.Float64, strict=False)
                den_no_zero = pl.when(den == 0).then(None).otherwise(den)
                df = df.with_columns((num / den_no_zero).alias(name))
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
                # ponytail: re importato in cima al file, regex più robusta con spazi
                f = formula.strip()
                m = re.match(r"^(year|month)\s*\(\s*(.+?)\s*\)$", f, flags=re.IGNORECASE)
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

        except Exception as e:
            warnings.append({"feature": name, "reason": f"Eccezione durante il calcolo: {str(e)}"})
            logger.exception(
                "Feature engineering fallita. Feature=%s, type=%s, sources=%s",
                name,
                feat_type,
                sources,
            )
            continue

    return df, added_cols, warnings


# ─────────────────────────────────────────────────────────────────────────────
# Data Cleaning
# ─────────────────────────────────────────────────────────────────────────────


def _is_string_like_dtype(dtype: Any) -> bool:
    name = str(dtype).lower()
    return any(token in name for token in ("string", "str", "utf8", "categorical", "enum"))


def _apply_single_action(frame: pl.DataFrame, act: CleaningAction | None) -> pl.DataFrame:
    """Applica una singola azione di pulizia al DataFrame."""
    if not act:
        return frame
    act_type = act.type
    params = act.params or {}
    col = act.column

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
        # ponytail: preserva il dtype originale invece di castare l'intera colonna a String
        original_dtype = frame.schema.get(col)
        source_str = pl.col(col).cast(pl.String, strict=False)
        if match_mode == "exact_case_insensitive_trimmed":
            match_expr = source_str.str.strip_chars().str.to_lowercase().is_in(normalized)
        else:
            match_expr = source_str.is_in([str(v) for v in values if v is not None])
        return frame.with_columns(
            pl.when(match_expr).then(pl.lit(None, dtype=original_dtype)).otherwise(pl.col(col)).alias(col)
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
    context: EdaContext | dict | None = None,
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
    if isinstance(context, EdaContext):
        context_dict = context.model_dump()
    elif isinstance(context, dict):
        context_dict = context
    else:
        context_dict = {}

    # ── 1. Feature Engineering (su df_full, non duplicate su df + df_full) ─────
    accepted_features: list[AcceptedFeature] = []
    for item in context_dict.get("accepted_features", []):
        if isinstance(item, AcceptedFeature):
            accepted_features.append(item)
        elif isinstance(item, dict):
            accepted_features.append(AcceptedFeature(**item))
        elif isinstance(item, str):
            accepted_features.append(AcceptedFeature(
                name=item, type="unknown", source_columns=[], formula="", status="accepted",
            ))

    added_cols = []
    if accepted_features:
        df_full, added_cols, _ = _compute_accepted_features(df_full, accepted_features)

    # ── 2. Cleaning (su df_full) ─────────────────────────────────────────────
    pre_clean_rows = len(df_full)
    pre_clean_cols = len(df_full.columns)

    cleaning_actions_raw = context_dict.get("cleaning_actions") or []
    cleaning_actions: list[CleaningAction] = []
    for act in cleaning_actions_raw:
        if isinstance(act, CleaningAction):
            cleaning_actions.append(act)
        elif isinstance(act, dict):
            cleaning_actions.append(CleaningAction(**act))
    for act in cleaning_actions:
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

    # ── 3. Campionamento (dopo le trasformazioni) ────────────────────────────
    df, sampled, sample_n = maybe_sample(df_full)

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
            "target": context_dict.get("target"),
            "problem_type": context_dict.get("problem_type"),
            "n_rows_full": len(df_full),
            "n_cols": len(df_full.columns),
            "sampled": sampled,
            "sample_n": sample_n,
            "semantic_types": semantic_types,
            "datetime_features": analyze_datetime_features(df, groups.get("datetime", [])),
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
                    context=context_dict,
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
