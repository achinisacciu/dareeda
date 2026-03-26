import json
import polars as pl
from datetime import datetime
from sqlalchemy.orm import Session

from api.models.orm import AnalysisRun, Dataset
from core.config import settings
from core.data_loader import load_file
from core.sampling import maybe_sample
from core.semantic_typer import type_dataframe, group_by_semantic
from eda.modules import overview, data_quality, univariate, bivariate, multivariate, timeseries, ml_exploratory, inference, insights, enterprise

MODULES = [
    ("overview",       "Panoramica dataset",   overview.run,        10),
    ("data_quality",   "Qualità del dato",     data_quality.run,    22),
    ("univariate",     "Analisi univariata",   univariate.run,      42),
    ("bivariate",      "Analisi bivariata",    bivariate.run,       58),
    ("multivariate",   "Analisi multivariata", multivariate.run,    68),
    ("timeseries",     "Serie temporali",      timeseries.run,      74),
    ("ml_exploratory", "ML esplorativo",       ml_exploratory.run,  88),
    ("inference",      "Inferenza statistica", inference.run,       96),
    ("insights",       "Insights finali",      insights.run,        99),
]


def _compute_accepted_features(df: pl.DataFrame, accepted: list) -> tuple[pl.DataFrame, list]:
    """
    Calcola le colonne derivate accettate dall'utente e le aggiunge al DataFrame.
    Restituisce (df_arricchito, lista_colonne_aggiunte).
    """
    added_cols = []

    for feature in accepted:
        name    = feature.get("name")
        formula = feature.get("formula", "")
        sources = feature.get("source_columns", [])

        if not name or not formula:
            continue

        # Verifica che le colonne sorgente esistano
        if not all(col in df.columns for col in sources):
            continue

        try:
            feat_type = feature.get("type", "")

            if feat_type == "revenue" and len(sources) == 2:
                # Cast permissivo: alcune sorgenti possono essere stringhe numeriche
                left = df[sources[0]].cast(pl.Float64, strict=False)
                right = df[sources[1]].cast(pl.Float64, strict=False)
                col = left * right
                df = df.with_columns(col.alias(name))
                added_cols.append(name)

            elif feat_type == "margin" and len(sources) == 2:
                left = df[sources[0]].cast(pl.Float64, strict=False)
                right = df[sources[1]].cast(pl.Float64, strict=False)
                col = left - right
                df = df.with_columns(col.alias(name))
                added_cols.append(name)

            elif feat_type == "margin_pct" and len(sources) == 2:
                sell = df[sources[0]].cast(pl.Float64, strict=False)
                cost = df[sources[1]].cast(pl.Float64, strict=False)
                col  = ((sell - cost) / sell.replace(0, None) * 100)
                df   = df.with_columns(col.alias(name))
                added_cols.append(name)

            elif feat_type in ("ratio",) and len(sources) == 2:
                num = df[sources[0]].cast(pl.Float64, strict=False)
                den = df[sources[1]].cast(pl.Float64, strict=False).replace(0, None)
                col = num / den
                df  = df.with_columns(col.alias(name))
                added_cols.append(name)

            elif feat_type == "discount" and len(sources) == 2:
                price    = df[sources[0]].cast(pl.Float64, strict=False)
                discount = df[sources[1]].cast(pl.Float64, strict=False)
                # Rileva se lo sconto è in scala 0-1 o 0-100
                d_max = discount.drop_nulls().max()
                if d_max is not None and d_max <= 1.0:
                    col = price * (1 - discount)
                else:
                    col = price * (1 - discount / 100)
                df = df.with_columns(col.alias(name))
                added_cols.append(name)

            elif feat_type == "derived_feature" and isinstance(formula, str):
                # Supporto per feature derivate generate dalle regole datetime (es. year(col), month(col))
                # Esempi formula: "year(data)" / "month(data)"
                f = formula.strip()
                import re
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
            # Se il calcolo fallisce, salta senza bloccare l'analisi
            continue

    return df, added_cols


def run_analysis(analysis_id: str, dataset_id: str, db: Session, context: dict = None) -> None:
    run     = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    run.status     = "running"
    run.started_at = datetime.utcnow()
    db.commit()

    try:
        filepath = settings.data_dir / dataset.filepath
        df_full  = load_file(filepath)
        df, sampled, sample_n = maybe_sample(df_full)

        context = context or {}

        # ── Feature accettate dall'utente ────────────────────────────────────
        # Priorità: 1) usare le definizioni complete dal DB (formula + source_columns)
        #           2) estendere con i nomi ricevuti dal context (robustezza se UI/DB non sono allineati)
        accepted_features = []
        accepted_by_name: dict[str, dict] = {}

        all_features = []
        if dataset.suggested_features:
            all_features = json.loads(dataset.suggested_features) or []
            for f in all_features:
                if f.get("status") == "accepted":
                    name = f.get("name")
                    if name:
                        accepted_by_name[name] = f

        if context and context.get("accepted_features"):
            context_names = context.get("accepted_features") or []
            if all_features:
                feature_map = {f.get("name"): f for f in all_features if f.get("name")}
            else:
                feature_map = {}

            for n in context_names:
                if not n:
                    continue
                if n in accepted_by_name:
                    continue
                # Se nel DB esiste la definizione completa, usala.
                if n in feature_map:
                    accepted_by_name[n] = feature_map[n]
                else:
                    # Fallback: definizione "minima" (può portare a skip del calcolo se mancano formula/source_columns)
                    accepted_by_name[n] = {
                        "name": n,
                        "type": "unknown",
                        "source_columns": [],
                        "formula": "",
                        "status": "accepted",
                    }

        accepted_features = list(accepted_by_name.values())

        # Calcola e aggiungi le colonne derivate al DataFrame
        added_cols = []
        if accepted_features:
            df, added_cols = _compute_accepted_features(df, accepted_features)
            # Aggiorna anche df_full con le stesse colonne (per moduli che lo usano)
            df_full, _ = _compute_accepted_features(df_full, accepted_features)

        # ── Applica azioni di pulizia (trasformazioni selezionate) ─────────
        # Importante: nessuna modifica automatica; solo azioni esplicite dell'utente.
        pre_clean_rows = len(df_full)
        pre_clean_cols = len(df_full.columns)

        def _is_string_like_dtype(dtype) -> bool:
            name = str(dtype).lower()
            return any(token in name for token in ("string", "str", "utf8", "categorical", "enum"))

        def _apply_single_action(frame: pl.DataFrame, act: dict) -> pl.DataFrame:
            act_type = (act or {}).get("type")
            params = (act or {}).get("params") or {}
            col = (act or {}).get("column")

            if act_type == "exclude_column":
                if col and col in frame.columns:
                    return frame.drop(col)
                return frame

            if act_type == "drop_duplicate_rows":
                # Deduplicazione esatta mantenendo la prima occorrenza
                return frame.unique(maintain_order=True)

            if act_type == "replace_values":
                if not col or col not in frame.columns:
                    return frame
                if not _is_string_like_dtype(frame.schema.get(col)):
                    return frame

                match_mode = params.get("match_mode") or "exact"
                values = params.get("values") or []
                normalized_targets = [str(v).strip().lower() for v in values if v is not None]
                if not normalized_targets:
                    return frame

                source = pl.col(col).cast(pl.String, strict=False)
                if match_mode == "exact_case_insensitive_trimmed":
                    match_expr = source.str.strip_chars().str.to_lowercase().is_in(normalized_targets)
                else:
                    match_expr = source.is_in([str(v) for v in values if v is not None])

                return frame.with_columns(
                    pl.when(match_expr)
                    .then(pl.lit(None, dtype=pl.String))
                    .otherwise(source)
                    .alias(col)
                )

            if act_type == "trim_whitespace":
                if not col or col not in frame.columns:
                    return frame
                if not _is_string_like_dtype(frame.schema.get(col)):
                    return frame

                source = pl.col(col).cast(pl.String, strict=False)
                return frame.with_columns(
                    pl.when(pl.col(col).is_null())
                    .then(pl.lit(None, dtype=pl.String))
                    .otherwise(source.str.strip_chars())
                    .alias(col)
                )

            return frame

        def _apply_cleaning_actions(df_in: pl.DataFrame, df_full_in: pl.DataFrame, actions: list[dict]):
            if not actions:
                return df_in, df_full_in

            df_out = df_in
            df_full_out = df_full_in

            for act in actions:
                df_out = _apply_single_action(df_out, act)
                df_full_out = _apply_single_action(df_full_out, act)

            return df_out, df_full_out

        cleaning_actions = context.get("cleaning_actions") or []
        df, df_full = _apply_cleaning_actions(df, df_full, cleaning_actions)
        cleaning_summary = {
            "actions": cleaning_actions,
            "before_rows": pre_clean_rows,
            "after_rows": len(df_full),
            "before_cols": pre_clean_cols,
            "after_cols": len(df_full.columns),
        }

        # ── Tipi semantici (aggiornati con le nuove colonne) ─────────────────
        semantic_types = type_dataframe(df)
        groups         = group_by_semantic(semantic_types)

        # Campione serializzato per permettere il rendering client-side in Multivariata
        # (salviamo tutte le colonne numeriche + la target se selezionata).
        sample_path = None
        sample_relpath = None
        try:
            result_dir = settings.data_dir / dataset.project_id
            result_dir.mkdir(parents=True, exist_ok=True)
            sample_path = result_dir / f"analysis_{analysis_id}_sample.parquet"

            numeric_cols = groups.get("numeric_continuous", []) + groups.get("numeric_discrete", [])
            numeric_cols = [c for c in numeric_cols if c in df.columns]
            target_col = context.get("target") if context else None

            sample_cols = list(numeric_cols)
            if target_col and target_col in df.columns:
                sample_cols.append(target_col)

            # Parquet richiede almeno una colonna: se non ci sono numerici (o target),
            # lasciamo perdere (Multivariata verrà marcata come "skipped").
            if sample_cols:
                df.select(sample_cols).write_parquet(sample_path)
                sample_relpath = str(sample_path.relative_to(settings.data_dir))
        except Exception:
            # Non blocchiamo l'analisi se la scrittura del campione fallisce.
            pass

        results = {
            "analysis_id":        analysis_id,
            "dataset_id":         dataset_id,
            "dataset_filename":   dataset.filename,
            "target":             context.get("target") if context else None,
            "problem_type":      context.get("problem_type") if context else None,
            "generated_at":       datetime.utcnow().isoformat(),
            "tool_version":       settings.app_version,
            "sampled":            sampled,
            "sample_n":           sample_n,
            "n_rows_full":        len(df_full),
            "n_cols":             len(df_full.columns),
            "semantic_types":     semantic_types,
            "derived_columns":    added_cols,   # colonne calcolate incluse
            "accepted_features":  accepted_features,
            "applied_cleaning":   cleaning_summary,
            "analysis_context": {
                "target": context.get("target") if context else None,
                "problem_type": context.get("problem_type") if context else None,
                "accepted_feature_names": [f.get("name") for f in accepted_features if f.get("name")],
                "cleaning_actions": cleaning_actions,
                "sampling": {
                    "sampled": sampled,
                    "sample_n": sample_n,
                    "full_rows_before_sampling": len(df_full),
                },
            },
        }

        for key, label, fn, progress in MODULES:
            run.current_module = label
            run.progress_pct   = max(0, progress - 5)
            db.commit()
            try:
                if key in ("ml_exploratory", "multivariate"):
                    results[key] = fn(
                        df=df, df_full=df_full,
                        semantic_types=semantic_types,
                        groups=groups,
                        context=context,
                    )
                else:
                    results[key] = fn(
                        df=df, df_full=df_full,
                        semantic_types=semantic_types,
                        groups=groups,
                    )
            except Exception as e:
                results[key] = {"error": str(e), "skipped": True}

            run.progress_pct = progress
            db.commit()

        result_dir = settings.data_dir / dataset.project_id
        result_dir.mkdir(parents=True, exist_ok=True)

        cleaned_export_path = result_dir / f"analysis_{analysis_id}_cleaned.parquet"
        cleaned_export_relpath = None
        cleaned_export_hash = None
        try:
            df_full.write_parquet(cleaned_export_path)
            cleaned_export_relpath = str(cleaned_export_path.relative_to(settings.data_dir))
            cleaned_export_hash = enterprise._sha256_file(cleaned_export_path)
        except Exception:
            cleaned_export_path = None

        dataset_hash = enterprise._sha256_file(filepath)
        runtime_seconds = 0.0
        if run.started_at:
            runtime_seconds = max((datetime.utcnow() - run.started_at).total_seconds(), 0.0)

        result_dir  = settings.data_dir / dataset.project_id
        result_path = result_dir / f"analysis_{analysis_id}.json"
        result_relpath = str(result_path.relative_to(settings.data_dir))

        results.update(
            enterprise.build_enterprise_outputs(
                df_full=df_full,
                semantic_types=semantic_types,
                groups=groups,
                base_results=results,
                dataset=dataset,
                filepath=filepath,
                target_col=context.get("target") if context else None,
                problem_type=context.get("problem_type") if context else None,
                accepted_features=accepted_features,
                dataset_hash=dataset_hash,
                cleaned_export_relpath=cleaned_export_relpath,
                cleaned_export_hash=cleaned_export_hash,
                sample_relpath=sample_relpath,
                result_relpath=result_relpath,
                runtime_seconds=runtime_seconds,
                tool_version=settings.app_version,
                working_dir=settings.data_dir.parent,
            )
        )

        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, default=str, indent=2)

        run.status         = "completed"
        run.progress_pct   = 100
        run.result_path    = result_relpath
        run.current_module = None
        run.completed_at   = datetime.utcnow()
        db.commit()

    except Exception as e:
        run.status        = "failed"
        run.error_message = str(e)
        db.commit()
        raise
