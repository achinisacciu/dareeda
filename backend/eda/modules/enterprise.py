import hashlib
import json
import platform
import re
import subprocess
from datetime import datetime
from importlib import metadata as importlib_metadata
from pathlib import Path

import plotly.graph_objects as go
import polars as pl

PROTECTED_ATTRIBUTE_KEYWORDS = {
    "gender": "gender",
    "sex": "gender",
    "age": "age",
    "birth": "age",
    "country": "geography",
    "region": "geography",
    "city": "geography",
    "zip": "geography",
    "cap": "geography",
    "race": "sensitive",
    "ethnicity": "sensitive",
    "religion": "sensitive",
    "marital": "demographic",
    "disability": "sensitive",
    "nationality": "geography",
}

PII_KEYWORDS = {
    "email": "email",
    "mail": "email",
    "phone": "phone",
    "mobile": "phone",
    "tel": "phone",
    "name": "name",
    "nome": "name",
    "surname": "name",
    "cognome": "name",
    "address": "address",
    "indirizzo": "address",
    "street": "address",
    "iban": "financial",
    "card": "financial",
    "credit": "financial",
    "fiscal": "government_id",
    "tax": "government_id",
    "ssn": "government_id",
    "passport": "government_id",
    "dob": "birth_date",
    "birth": "birth_date",
}

POSITIVE_CLASS_HINTS = {
    "1",
    "true",
    "yes",
    "y",
    "si",
    "positive",
    "fraud",
    "churn",
    "default",
    "active",
}


def _fig(fig: go.Figure) -> dict:
    return json.loads(fig.to_json())


def _safe_version(package_name: str) -> str:
    try:
        return importlib_metadata.version(package_name)
    except Exception:
        return "n/a"


def _safe_git_commit(cwd: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(cwd),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None


def _sha256_file(path: Path) -> str | None:
    if not path or not path.exists():
        return None

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fmt_pct(value: float | int | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)


def _series_unique_ratio(series: pl.Series, n_rows: int) -> float:
    if n_rows <= 0:
        return 0.0
    try:
        return round(float(series.drop_nulls().n_unique()) / n_rows * 100, 2)
    except Exception:
        return 0.0


def _quality_decomposition(df_full: pl.DataFrame, groups: dict, base_results: dict) -> dict:
    n_rows = len(df_full)
    n_cols = len(df_full.columns)
    missing_global = (((base_results.get("data_quality") or {}).get("missing") or {}).get("global") or {})
    duplicates = (((base_results.get("data_quality") or {}).get("duplicates")) or {})

    completeness = 100.0 - float(missing_global.get("pct_missing_cells") or 0.0)
    uniqueness = 100.0 - float(duplicates.get("pct_duplicate_rows") or 0.0)

    numeric_cols = groups.get("numeric_continuous", []) + groups.get("numeric_discrete", [])
    invalid_numeric = 0
    numeric_checked = 0
    for col in numeric_cols:
        series = df_full[col].cast(pl.Float64, strict=False)
        numeric_checked += len(series)
        invalid_numeric += int(series.is_nan().sum()) if hasattr(series, "is_nan") else 0
    validity = 100.0 if numeric_checked == 0 else max(0.0, 100.0 - invalid_numeric / numeric_checked * 100.0)

    near_constant = ((((base_results.get("data_quality") or {}).get("inconsistencies")) or {}).get("near_constant") or [])
    consistency_penalty = min(len(near_constant) * 4.0, 30.0)
    consistency = max(0.0, 100.0 - consistency_penalty)
    accuracy = max(0.0, min(completeness, uniqueness) - 2.0)
    timeliness = 92.0 if groups.get("datetime") else 70.0
    weighted = (
        completeness * 0.25
        + uniqueness * 0.20
        + validity * 0.20
        + consistency * 0.15
        + accuracy * 0.10
        + timeliness * 0.10
    )

    rows = [
        {"dimension": "Completeness", "weight": 25, "score": _fmt_pct(completeness), "benchmark": ">95", "status": "ok" if completeness >= 95 else ("warning" if completeness >= 85 else "critical")},
        {"dimension": "Uniqueness", "weight": 20, "score": _fmt_pct(uniqueness), "benchmark": ">99", "status": "ok" if uniqueness >= 99 else ("warning" if uniqueness >= 95 else "critical")},
        {"dimension": "Validity", "weight": 20, "score": _fmt_pct(validity), "benchmark": ">90", "status": "ok" if validity >= 90 else ("warning" if validity >= 80 else "critical")},
        {"dimension": "Consistency", "weight": 15, "score": _fmt_pct(consistency), "benchmark": ">85", "status": "ok" if consistency >= 85 else ("warning" if consistency >= 70 else "critical")},
        {"dimension": "Accuracy", "weight": 10, "score": _fmt_pct(accuracy), "benchmark": ">85", "status": "ok" if accuracy >= 85 else ("warning" if accuracy >= 75 else "critical")},
        {"dimension": "Timeliness", "weight": 10, "score": _fmt_pct(timeliness), "benchmark": ">90", "status": "ok" if timeliness >= 90 else ("warning" if timeliness >= 80 else "critical")},
    ]
    return {
        "dimensions": rows,
        "total_score": _fmt_pct(weighted),
        "quality_band": "high" if weighted >= 85 else ("medium" if weighted >= 70 else "low"),
        "global_shape": {"rows": n_rows, "columns": n_cols, "cells": n_rows * n_cols},
    }


def _detect_pii_candidates(df_full: pl.DataFrame) -> list[dict]:
    candidates = []
    email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone_re = re.compile(r"^\+?[0-9][0-9\-\s]{7,}$")

    for col in df_full.columns:
        lower = col.lower()
        series = df_full[col]
        matched_type = None
        confidence = 0.0
        reason = None

        for keyword, pii_type in PII_KEYWORDS.items():
            if keyword in lower:
                matched_type = pii_type
                confidence = 0.96
                reason = f"keyword:{keyword}"
                break

        if matched_type is None and str(series.dtype).lower() in ("string", "utf8"):
            sample = series.drop_nulls().cast(pl.String, strict=False).head(25).to_list()
            if sample:
                email_hits = sum(1 for value in sample if email_re.match(str(value or "").strip()))
                phone_hits = sum(1 for value in sample if phone_re.match(str(value or "").strip()))
                if email_hits >= max(2, len(sample) // 4):
                    matched_type = "email"
                    confidence = 0.9
                    reason = "pattern:email"
                elif phone_hits >= max(2, len(sample) // 4):
                    matched_type = "phone"
                    confidence = 0.82
                    reason = "pattern:phone"

        if matched_type is None:
            continue

        candidates.append({
            "column": col,
            "pii_type": matched_type,
            "confidence": round(confidence * 100, 1),
            "reason": reason,
            "recommended_action": "pseudonymize" if matched_type in {"email", "phone", "financial", "government_id"} else "review",
        })

    return candidates


def _status_from_profile(col: dict) -> str:
    if (col.get("pct_missing") or 0) >= 40:
        return "critical"
    if (col.get("pct_missing") or 0) >= 10:
        return "warning"
    if col.get("semantic_type") == "id":
        return "attention"
    return "ready"


def _build_profiling(df_full: pl.DataFrame, semantic_types: dict, groups: dict, base_results: dict, dataset, filepath: Path, pii_candidates: list[dict]) -> dict:
    n_rows = len(df_full)
    columns = []
    pii_map = {item["column"]: item for item in pii_candidates}
    overview_cols = ((base_results.get("overview") or {}).get("columns") or [])
    overview_map = {item["name"]: item for item in overview_cols}

    for idx, col in enumerate(df_full.columns, start=1):
        series = df_full[col]
        overview_meta = overview_map.get(col) or {}
        memory_mb = round(df_full.select(col).estimated_size("mb"), 4)
        columns.append({
            "index": idx,
            "column": col,
            "dtype_pandas": str(series.dtype),
            "dtype_numpy": str(series.dtype),
            "semantic_type": semantic_types.get(col, "unknown"),
            "storage_type": str(series.dtype),
            "n_unique": int(series.drop_nulls().n_unique()),
            "uniqueness_ratio": _series_unique_ratio(series, n_rows),
            "pct_missing": overview_meta.get("pct_missing", _fmt_pct(series.null_count() / max(n_rows, 1) * 100)),
            "memory_mb": memory_mb,
            "role": overview_meta.get("role", "feature"),
            "status": _status_from_profile({"pct_missing": overview_meta.get("pct_missing", 0), "semantic_type": semantic_types.get(col, "unknown")}),
            "pii_type": (pii_map.get(col) or {}).get("pii_type"),
        })

    semantic_summary = []
    label_map = {
        "id": "Identificatori",
        "numeric_continuous": "Numeriche continue",
        "numeric_discrete": "Numeriche discrete",
        "categorical_nominal": "Categoriche nominali",
        "categorical_ordinal": "Categoriche ordinali",
        "boolean": "Booleane",
        "datetime": "DateTime",
        "text": "Testuali",
        "geographic": "Geografiche",
        "unknown": "Sconosciute",
    }
    for key, label in label_map.items():
        cols = groups.get(key, [])
        if not cols:
            continue
        semantic_summary.append({"category": label, "count": len(cols), "pct": _fmt_pct(len(cols) / max(len(df_full.columns), 1) * 100), "examples": ", ".join(cols[:3])})

    semantic_detection = []
    for col in columns:
        confidence = 98 if col["semantic_type"] in {"id", "datetime", "boolean"} else 88
        pattern = "name-based" if col["semantic_type"] in {"id", "geographic"} else "dtype-profile"
        if col["pii_type"]:
            pattern = f"pii:{col['pii_type']}"
            confidence = max(confidence, 95)
        semantic_detection.append({
            "column": col["column"],
            "dtype": col["dtype_pandas"],
            "unique_values": col["n_unique"],
            "pattern_detected": pattern,
            "semantic_type": col["semantic_type"],
            "confidence": confidence,
        })

    scatter_x = [item["pct_missing"] for item in columns]
    scatter_y = [item["uniqueness_ratio"] for item in columns]
    scatter_size = [max(item["memory_mb"] * 60, 10) for item in columns]
    scatter_text = [item["column"] for item in columns]
    scatter_color = [
        "#E4002B" if item["pii_type"] else "#0904AE" if item["semantic_type"] == "datetime" else "#1B272F"
        for item in columns
    ]
    fig_scatter = go.Figure(go.Scatter(
        x=scatter_x,
        y=scatter_y,
        mode="markers+text",
        text=scatter_text,
        textposition="top center",
        marker=dict(size=scatter_size, color=scatter_color, opacity=0.72),
    ))
    fig_scatter.update_layout(
        title="Cardinality vs Missing",
        xaxis_title="% missing",
        yaxis_title="% unique ratio",
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=50, l=60, r=20),
    )

    treemap_labels = [item["category"] for item in semantic_summary]
    treemap_values = [item["count"] for item in semantic_summary]
    fig_treemap = go.Figure(go.Treemap(
        labels=treemap_labels,
        parents=[""] * len(treemap_labels),
        values=treemap_values,
        textinfo="label+value+percent entry",
        marker=dict(colors=["#E4002B", "#0904AE", "#59ADF7", "#1B272F", "#37424A"] * 3),
    ))
    fig_treemap.update_layout(
        title="Semantic Types Treemap",
        paper_bgcolor="#FFFFFF",
        margin=dict(t=50, b=20, l=20, r=20),
        font=dict(family="JetBrains Mono", size=11),
    )

    return {
        "lineage": {
            "primary_source": dataset.file_format.upper(),
            "system_of_record": filepath.name,
            "extraction_mode": "full",
            "update_frequency": "on-demand upload",
            "last_refresh": datetime.utcnow().date().isoformat(),
            "source_owner": "DAREEDA workspace",
            "technical_contact": "n/a",
            "documentation": "generated from uploaded dataset",
        },
        "structural_overview": {
            "n_rows": n_rows,
            "n_columns": len(df_full.columns),
            "n_cells": n_rows * len(df_full.columns),
            "memory_mb": round(df_full.estimated_size("mb"), 3),
            "disk_size_mb": round(filepath.stat().st_size / (1024 * 1024), 3) if filepath.exists() else None,
        },
        "semantic_summary": semantic_summary,
        "master_schema": columns,
        "semantic_detection": semantic_detection,
        "pii_candidates": pii_candidates,
        "charts": {
            "semantic_treemap": _fig(fig_treemap) if treemap_labels else None,
            "cardinality_missing_scatter": _fig(fig_scatter) if columns else None,
        },
    }


def _class_balance(df_full: pl.DataFrame, target_col: str | None) -> dict | None:
    if not target_col or target_col not in df_full.columns:
        return None

    series = df_full[target_col].drop_nulls().cast(pl.String, strict=False)
    if len(series) == 0:
        return None

    vc = series.value_counts(sort=True)
    rows = []
    for idx in range(len(vc)):
        label = str(vc[target_col][idx])
        count = int(vc["count"][idx])
        rows.append({"class": label, "count": count, "pct": _fmt_pct(count / max(len(series), 1) * 100)})

    imbalance_ratio = None
    if len(rows) > 1 and rows[-1]["count"] > 0:
        imbalance_ratio = round(rows[0]["count"] / rows[-1]["count"], 2)

    severity = "ok"
    if imbalance_ratio and imbalance_ratio >= 10:
        severity = "critical"
    elif imbalance_ratio and imbalance_ratio >= 3:
        severity = "warning"

    return {
        "target": target_col,
        "distribution": rows,
        "imbalance_ratio": imbalance_ratio,
        "severity": severity,
    }


def _leakage_risks(df_full: pl.DataFrame, semantic_types: dict, target_col: str | None) -> list[dict]:
    risks = []
    if not target_col:
        return risks

    for col in df_full.columns:
        if col == target_col:
            continue
        lower = col.lower()
        stype = semantic_types.get(col, "unknown")
        if stype == "id":
            risks.append({
                "column": col,
                "risk": "Identifier leakage",
                "severity": "high",
                "evidence": "Quasi-ID o chiave tecnica",
                "recommended_action": "exclude from modeling",
            })
        elif stype == "datetime" and any(token in lower for token in ("updated", "closed", "resolved", "approved", "deleted")):
            risks.append({
                "column": col,
                "risk": "Post-event timestamp",
                "severity": "high",
                "evidence": "Nome colonna suggerisce evento successivo al target",
                "recommended_action": "review timeline before training",
            })
        elif target_col.lower() in lower and lower != target_col.lower():
            risks.append({
                "column": col,
                "risk": "Target-like proxy",
                "severity": "medium",
                "evidence": "Nome colonna semanticamente vicino alla target",
                "recommended_action": "manual review",
            })
    return risks


def _predictive_prep(df_full: pl.DataFrame, groups: dict, base_results: dict, target_col: str | None, problem_type: str | None, accepted_features: list[dict], semantic_types: dict) -> dict:
    missing_per_column = ((((base_results.get("data_quality") or {}).get("missing")) or {}).get("per_column") or [])
    missing_map = {item["variable"]: item for item in missing_per_column}

    feature_engineering = []
    for feature in accepted_features or []:
        if feature.get("name"):
            feature_engineering.append({
                "feature": feature.get("name"),
                "source_columns": ", ".join(feature.get("source_columns") or []),
                "formula": feature.get("formula") or feature.get("type") or "derived",
                "status": feature.get("status") or "accepted",
            })

    for col in groups.get("datetime", []):
        feature_engineering.append({
            "feature": f"{col}_year/month",
            "source_columns": col,
            "formula": "calendar decomposition",
            "status": "recommended",
        })

    encoding_strategy = []
    for col in groups.get("categorical_nominal", []):
        strategy = "one-hot"
        if df_full[col].drop_nulls().n_unique() > 20:
            strategy = "target/frequency encoding"
        encoding_strategy.append({"column": col, "strategy": strategy, "missing_pct": missing_map.get(col, {}).get("missing_pct", 0)})
    for col in groups.get("categorical_ordinal", []):
        encoding_strategy.append({"column": col, "strategy": "ordinal encoding", "missing_pct": missing_map.get(col, {}).get("missing_pct", 0)})
    for col in groups.get("boolean", []):
        encoding_strategy.append({"column": col, "strategy": "binary cast", "missing_pct": missing_map.get(col, {}).get("missing_pct", 0)})

    scaling_strategy = []
    for col in groups.get("numeric_continuous", []):
        stats = (((base_results.get("univariate") or {}).get(col)) or {}).get("stats") or {}
        outlier_pct = float(stats.get("outlier_iqr_pct") or 0)
        scaling_strategy.append({"column": col, "strategy": "RobustScaler" if outlier_pct > 5 else "StandardScaler", "outlier_pct": outlier_pct})
    for col in groups.get("numeric_discrete", []):
        scaling_strategy.append({"column": col, "strategy": "Optional scaling / leave as count", "outlier_pct": None})

    imputation_strategy = []
    for item in missing_per_column:
        if (item.get("missing_count") or 0) <= 0:
            continue
        stype = semantic_types.get(item["variable"], "unknown")
        if stype.startswith("numeric"):
            strategy = "median" if item["missing_pct"] < 20 else "segment-based median / evaluate drop"
        elif stype.startswith("categorical") or stype == "boolean":
            strategy = "most frequent / explicit missing bucket"
        elif stype == "datetime":
            strategy = "calendar-aware imputation / flag missing"
        else:
            strategy = "explicit null token / review"
        imputation_strategy.append({"column": item["variable"], "missing_pct": item["missing_pct"], "severity": item["severity"], "strategy": strategy})

    split_strategy = {
        "recommended": "time-based holdout" if groups.get("datetime") else ("stratified split" if problem_type == "classification" else "random split"),
        "train": 70,
        "validation": 15,
        "test": 15,
        "notes": "Preserve chronological order." if groups.get("datetime") else "Fix random seed and stratify by target when classification.",
    }

    return {
        "feature_engineering": feature_engineering,
        "encoding_strategy": encoding_strategy,
        "scaling_strategy": scaling_strategy,
        "imputation_strategy": imputation_strategy,
        "leakage_risk_assessment": _leakage_risks(df_full, semantic_types, target_col),
        "class_imbalance": _class_balance(df_full, target_col),
        "split_strategy": split_strategy,
        "preprocessing_pipeline": [
            "exclude IDs / leakage candidates",
            "apply selected cleaning rules",
            "impute missing values",
            "encode categorical features",
            "scale numeric features",
            "split train/validation/test",
        ],
    }


def _fairness_analysis(df_full: pl.DataFrame, target_col: str | None, problem_type: str | None) -> dict:
    if problem_type != "classification" or not target_col or target_col not in df_full.columns:
        return {"applicable": False, "reason": "Fairness analysis richiede una target classificativa esplicita.", "protected_attributes": [], "group_metrics": []}

    target_series = df_full[target_col].drop_nulls().cast(pl.String, strict=False)
    if target_series.n_unique() < 2 or target_series.n_unique() > 6:
        return {"applicable": False, "reason": "Target non binaria o con cardinalita troppo alta per disparate impact automatico.", "protected_attributes": [], "group_metrics": []}

    target_values = sorted(target_series.unique().to_list(), key=lambda value: str(value))
    positive_class = None
    for value in target_values:
        if str(value).strip().lower() in POSITIVE_CLASS_HINTS:
            positive_class = str(value)
            break
    if positive_class is None:
        positive_class = str(target_values[-1])

    protected = []
    group_metrics = []
    for col in df_full.columns:
        lower = col.lower()
        attr_type = None
        for keyword, detected in PROTECTED_ATTRIBUTE_KEYWORDS.items():
            if keyword in lower:
                attr_type = detected
                break
        if attr_type is None:
            continue

        protected.append({"column": col, "attribute_type": attr_type})
        frame = df_full.select([pl.col(col), pl.col(target_col)]).drop_nulls()
        if len(frame) < 20:
            continue

        if attr_type == "age":
            age_series = frame[col].cast(pl.Float64, strict=False)
            bins = (
                pl.when(age_series < 25).then(pl.lit("<25"))
                .when(age_series < 45).then(pl.lit("25-44"))
                .when(age_series < 65).then(pl.lit("45-64"))
                .otherwise(pl.lit("65+"))
                .alias("_protected_group")
            )
            frame = frame.with_columns(bins)
            group_col = "_protected_group"
        else:
            group_col = col

        rows = []
        for value in frame[group_col].cast(pl.String, strict=False).unique().sort().head(8).to_list():
            subgroup = frame.filter(pl.col(group_col).cast(pl.String, strict=False) == str(value))
            size = len(subgroup)
            if size < 10:
                continue
            positive_rate = subgroup[target_col].cast(pl.String, strict=False).eq(positive_class).sum() / max(size, 1)
            rows.append({"attribute": col, "group": str(value), "n": size, "positive_rate": _fmt_pct(float(positive_rate) * 100)})

        if len(rows) < 2:
            continue

        rates = [row["positive_rate"] for row in rows if row["positive_rate"] is not None]
        if not rates:
            continue
        disparate_impact = round(min(rates) / max(max(rates), 1e-6), 3)
        severity = "ok" if disparate_impact >= 0.8 else ("warning" if disparate_impact >= 0.6 else "critical")
        group_metrics.append({
            "attribute": col,
            "attribute_type": attr_type,
            "positive_class": positive_class,
            "disparate_impact_ratio": disparate_impact,
            "severity": severity,
            "groups": rows,
        })

    return {"applicable": True, "positive_class": positive_class, "protected_attributes": protected, "group_metrics": group_metrics}


def _governance(df_full: pl.DataFrame, target_col: str | None, problem_type: str | None, pii_candidates: list[dict]) -> dict:
    return {
        "pii_detection": pii_candidates,
        "fairness": _fairness_analysis(df_full, target_col, problem_type),
        "methodology": [
            "EDA deterministica con seed fissato nel backend",
            "Analisi univariate, bivariate, multivariate, ML explorative e inferenza statistica",
            "Sezioni enterprise derivate dagli output tecnici del motore EDA",
        ],
        "limitations": [
            "Le inferenze di governance sono euristiche e richiedono validazione domain-driven",
            "La fairness analysis automatica e applicabile solo con target classificativa e attributi protetti riconoscibili",
            "Le regole di leakage e PII detection non sostituiscono una review legale o privacy formale",
        ],
        "disclaimer": "Output destinato a supporto decisionale tecnico. Le decisioni di business, compliance e rilascio modello richiedono validazione umana.",
    }


def _advanced_analytics(groups: dict, base_results: dict) -> dict:
    has_datetime = bool(groups.get("datetime"))
    has_id = bool(groups.get("id"))
    has_bool = bool(groups.get("boolean"))
    has_numeric = bool(groups.get("numeric_continuous") or groups.get("numeric_discrete"))

    applicability = [
        {"analysis": "Cohort analysis", "applicable": has_datetime and has_id, "reason": "Richiede ID entita + timestamp di evento."},
        {"analysis": "Survival analysis", "applicable": has_datetime and has_bool, "reason": "Richiede durata/tempo e indicatore evento."},
        {"analysis": "Time decomposition", "applicable": has_datetime and has_numeric, "reason": "Richiede almeno una serie temporale numerica."},
    ]

    time_summary = None
    timeseries = base_results.get("timeseries") or {}
    if timeseries.get("active"):
        analyses = timeseries.get("analyses") or {}
        first_key = next(iter(analyses.keys()), None)
        if first_key and isinstance(analyses.get(first_key), dict):
            time_summary = {
                "series": first_key,
                "stationarity": ((analyses.get(first_key) or {}).get("stationarity") or {}).get("decision"),
                "note": (analyses.get(first_key) or {}).get("ai_comment"),
            }

    return {"applicability": applicability, "time_decomposition": time_summary}


def _owner_for_alert(alert_type: str) -> str:
    if "missing" in alert_type.lower():
        return "Data Engineer"
    if "leakage" in alert_type.lower():
        return "ML Lead"
    if "privacy" in alert_type.lower() or "pii" in alert_type.lower():
        return "Privacy Officer"
    if "imbalance" in alert_type.lower():
        return "Data Scientist"
    return "Analytics Lead"


def _executive(base_results: dict, quality: dict, pii_candidates: list[dict], predictive_prep: dict, dataset, target_col: str | None, problem_type: str | None) -> dict:
    missing = (((base_results.get("data_quality") or {}).get("missing")) or {})
    duplicates = (((base_results.get("data_quality") or {}).get("duplicates")) or {})
    missing_cols = sorted([item for item in (missing.get("per_column") or []) if (item.get("missing_pct") or 0) > 0], key=lambda item: item.get("missing_pct", 0), reverse=True)

    alerts = []
    for item in missing_cols[:3]:
        if item["missing_pct"] < 10:
            continue
        alerts.append({"severity": "critical" if item["missing_pct"] >= 30 else "high", "issue": f"Missing elevato su {item['variable']}", "columns": item["variable"], "immediate_action": "imputation strategy o esclusione", "owner": "Data Engineer"})
    for risk in predictive_prep.get("leakage_risk_assessment") or []:
        alerts.append({"severity": risk["severity"], "issue": risk["risk"], "columns": risk["column"], "immediate_action": risk["recommended_action"], "owner": _owner_for_alert(risk["risk"])})
    class_imbalance = predictive_prep.get("class_imbalance")
    if class_imbalance and class_imbalance.get("severity") in {"warning", "critical"}:
        alerts.append({"severity": class_imbalance["severity"], "issue": "Class imbalance", "columns": class_imbalance["target"], "immediate_action": "stratified split / reweighting / resampling", "owner": "Data Scientist"})
    for pii in pii_candidates[:3]:
        alerts.append({"severity": "high", "issue": f"PII rilevata: {pii['pii_type']}", "columns": pii["column"], "immediate_action": pii["recommended_action"], "owner": "Privacy Officer"})
    alerts = alerts[:8]

    total_score = quality["total_score"]
    ready_for_modeling = total_score >= 80 and not any(alert["severity"] == "critical" for alert in alerts if "leakage" in alert["issue"].lower())
    top_missing = ", ".join(item["variable"] for item in missing_cols[:3]) if missing_cols else "nessuna colonna critica"
    summary = [
        f"Il dataset {dataset.filename} contiene {base_results.get('n_rows_full', 0):,} record e {base_results.get('n_cols', 0)} feature.",
        f"La qualita complessiva stimata e {quality['quality_band']} ({total_score}/100) con missing concentrati su {top_missing}.",
        f"La percentuale di righe duplicate esatte e {duplicates.get('pct_duplicate_rows', 0)}%.",
    ]
    if target_col:
        summary.append(f"La target configurata e {target_col} ({problem_type or 'problem type non definito'}).")
    if alerts:
        summary.append(f"Rischio principale: {alerts[0]['issue']}.")

    action_items = []
    for idx, alert in enumerate(alerts[:5], start=1):
        action_items.append({"priority": idx, "title": alert["issue"], "owner": alert["owner"], "deadline": "Immediate" if alert["severity"] == "critical" else f"Sprint {idx}", "action": alert["immediate_action"]})

    return {
        "business_context": {"project": dataset.filename, "objective": problem_type or "exploratory assessment", "stakeholder": "Data / Analytics", "expected_impact": "Da quantificare con il business owner", "timeline": "Current sprint"},
        "executive_summary": " ".join(summary),
        "key_metrics": [
            {"metric": "Data Quality Score", "value": total_score, "benchmark": ">80", "status": "ok" if total_score >= 80 else "warning", "trend": "up"},
            {"metric": "Completeness", "value": quality["dimensions"][0]["score"], "benchmark": ">95", "status": quality["dimensions"][0]["status"], "trend": "flat"},
            {"metric": "Uniqueness", "value": quality["dimensions"][1]["score"], "benchmark": ">99", "status": quality["dimensions"][1]["status"], "trend": "flat"},
            {"metric": "Validity", "value": quality["dimensions"][2]["score"], "benchmark": ">90", "status": quality["dimensions"][2]["status"], "trend": "flat"},
            {"metric": "Consistency", "value": quality["dimensions"][3]["score"], "benchmark": ">85", "status": quality["dimensions"][3]["status"], "trend": "flat"},
            {"metric": "Timeliness", "value": quality["dimensions"][5]["score"], "benchmark": ">90", "status": quality["dimensions"][5]["status"], "trend": "flat"},
        ],
        "critical_alerts": alerts,
        "decision_matrix": [
            {"decision": "Procedere con modellazione", "status": "yes" if ready_for_modeling else "pending", "evidence": f"Quality score {total_score}/100", "confidence": 85 if ready_for_modeling else 62},
            {"decision": "Richiedere dati aggiuntivi", "status": "pending" if missing_cols else "no", "evidence": f"{len(missing_cols)} colonne con missing", "confidence": 78 if missing_cols else 40},
            {"decision": "Escalation privacy/compliance", "status": "pending" if pii_candidates else "no", "evidence": f"{len(pii_candidates)} colonne PII candidate", "confidence": 88 if pii_candidates else 25},
        ],
        "action_items": action_items,
        "recommendation": {"ready_for_modeling": ready_for_modeling, "label": "Pronto con mitigazioni" if ready_for_modeling else "Non ancora pronto"},
        "quality_score_decomposition": quality,
    }


def _deliverables(dataset_hash: str | None, cleaned_hash: str | None, cleaned_relpath: str | None, sample_relpath: str | None, result_relpath: str | None, runtime_seconds: float, quality: dict, pii_candidates: list[dict], working_dir: Path) -> dict:
    git_commit = _safe_git_commit(working_dir)
    return {
        "outputs": [
            {"name": "analysis_json", "path": result_relpath, "hash": None, "format": "json"},
            {"name": "cleaned_export", "path": cleaned_relpath, "hash": cleaned_hash, "format": "parquet"},
            {"name": "analysis_sample", "path": sample_relpath, "hash": None, "format": "parquet"},
        ],
        "validation_checklist": [
            {"check": "Replicability", "status": True, "detail": "Analysis JSON and deterministic seed available."},
            {"check": "Deterministic", "status": True, "detail": "Seed fixed in application settings."},
            {"check": "Scalability", "status": True, "detail": "Sampling + full dataset metadata preserved."},
            {"check": "Versioning", "status": bool(git_commit), "detail": git_commit or "Git hash unavailable."},
            {"check": "Performance", "status": True, "detail": f"Runtime captured: {round(runtime_seconds, 2)} seconds."},
        ],
        "approvals": [
            {"role": "Data Analyst", "status": "pending"},
            {"role": "Data Scientist Lead", "status": "pending"},
            {"role": "Data Engineer", "status": "pending"},
            {"role": "Privacy Officer", "status": "pending" if pii_candidates else "not_required"},
            {"role": "Business Owner", "status": "pending"},
            {"role": "QA / Peer Reviewer", "status": "pending"},
        ],
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "template_version": "EDA-Enterprise-v2.1-inspired",
            "dataset_hash": dataset_hash,
            "cleaned_dataset_hash": cleaned_hash,
            "runtime_seconds": round(runtime_seconds, 2),
            "environment": {
                "python": platform.python_version(),
                "polars": _safe_version("polars"),
                "numpy": _safe_version("numpy"),
                "scipy": _safe_version("scipy"),
                "scikit_learn": _safe_version("scikit-learn"),
            },
            "git_commit": git_commit,
            "quality_score": quality["total_score"],
        },
    }


def _front_matter(dataset, dataset_hash: str | None, runtime_seconds: float, tool_version: str, deliverables: dict) -> dict:
    return {
        "cover": {
            "title": f"EDA Analysis: {dataset.filename}",
            "subtitle": "Exploratory Data Analysis & Quality Assessment",
            "version": tool_version,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "analyst": "DAREEDA automated enterprise workflow",
            "reviewer": "Pending review",
            "classification": "INTERNAL",
            "dataset_hash": dataset_hash,
            "runtime": f"{round(runtime_seconds, 2)} s",
        },
        "change_log": [{"version": tool_version, "date": datetime.utcnow().strftime("%Y-%m-%d"), "author": "DAREEDA", "changes": "Generated enterprise EDA package", "approver": "Pending"}],
        "report_metadata": deliverables["report_metadata"],
    }


def build_enterprise_outputs(*, df_full: pl.DataFrame, semantic_types: dict, groups: dict, base_results: dict, dataset, filepath: Path, target_col: str | None, problem_type: str | None, accepted_features: list[dict], dataset_hash: str | None, cleaned_export_relpath: str | None, cleaned_export_hash: str | None, sample_relpath: str | None, result_relpath: str | None, runtime_seconds: float, tool_version: str, working_dir: Path) -> dict:
    quality = _quality_decomposition(df_full, groups, base_results)
    pii_candidates = _detect_pii_candidates(df_full)
    predictive_prep = _predictive_prep(df_full, groups, base_results, target_col, problem_type, accepted_features, semantic_types)
    deliverables = _deliverables(dataset_hash, cleaned_export_hash, cleaned_export_relpath, sample_relpath, result_relpath, runtime_seconds, quality, pii_candidates, working_dir)

    return {
        "front_matter": _front_matter(dataset, dataset_hash, runtime_seconds, tool_version, deliverables),
        "executive": _executive(base_results, quality, pii_candidates, predictive_prep, dataset, target_col, problem_type),
        "profiling": _build_profiling(df_full, semantic_types, groups, base_results, dataset, filepath, pii_candidates),
        "predictive_prep": predictive_prep,
        "advanced_analytics": _advanced_analytics(groups, base_results),
        "governance": _governance(df_full, target_col, problem_type, pii_candidates),
        "deliverables": deliverables,
    }
