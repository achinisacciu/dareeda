import json

import numpy as np
import plotly.graph_objects as go
import polars as pl
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.metrics import silhouette_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import LabelEncoder, StandardScaler


def _fig(f):
    return json.loads(f.to_json())


def validate_target(df, target_col):
    if target_col not in df.columns:
        return False, "Target non esiste nel dataset"
    if df[target_col].null_count() == len(df):
        return False, "Target completamente vuota"
    return True, None


def run(df, df_full, semantic_types, groups, context=None):
    if context is None:
        context = {}

    target_col = context.get("target")
    is_valid, error = validate_target(df, target_col)
    problem_type = context.get("problem_type")
    num_cols = groups.get("numeric_continuous", []) + groups.get("numeric_discrete", [])
    feature_cols = [c for c in num_cols if c != target_col]

    result = {
        "clustering": _clustering(df, feature_cols or num_cols),
        "anomaly_detection": _anomaly(df, feature_cols or num_cols),
    }

    if not target_col:
        result["error"] = "Target non definita"
        result["feature_importance"] = {"skipped": True, "reason": "Target non definita"}
        return result

    if not is_valid:
        result["error"] = error
        result["feature_importance"] = {"skipped": True, "reason": error}
        return result

    if problem_type not in ["classification", "regression"]:
        result["error"] = "Tipo problema non valido"
        result["feature_importance"] = {"skipped": True, "reason": "Tipo problema non valido"}
        return result

    is_class = problem_type == "classification"
    result["feature_importance"] = _mutual_info(df, feature_cols, target_col, is_class)
    return result


# ── Feature importance (Mutual Information) ────────────────────────────────


def _mutual_info(df, feature_cols, target_col, is_class):
    if len(feature_cols) < 1:
        return {"skipped": True, "reason": "Troppe poche feature numeriche"}

    try:
        feature_cols = feature_cols[:15]

        # ponytail: drop_nulls invece di fill_null per non distorcere varianza
        mat = df.select([
            pl.col(c).cast(pl.Float64) for c in feature_cols
        ]).drop_nulls().to_numpy()
        if len(mat) < 20:
            return {"skipped": True, "reason": "Dati insufficienti dopo rimozione NaN"}

        if is_class:
            # ponytail: drop_nulls() senza subset per droppare null anche sul target
            clean = df.select([
                pl.col(c).cast(pl.Float64) for c in feature_cols
            ] + [pl.col(target_col)])
            clean = clean.drop_nulls()
            mat = clean.select([pl.col(c) for c in feature_cols]).to_numpy()
            y_raw = clean[target_col].cast(pl.String).to_numpy().astype(str)
            y = LabelEncoder().fit_transform(y_raw)
            mi = mutual_info_classif(mat, y, random_state=42)
        else:
            clean = df.select([
                pl.col(c).cast(pl.Float64) for c in feature_cols
            ] + [pl.col(target_col).cast(pl.Float64)])
            clean = clean.drop_nulls()
            mat = clean.select([pl.col(c) for c in feature_cols]).to_numpy()
            y = clean[target_col].to_numpy()
            mi = mutual_info_regression(mat, y, random_state=42)

        results = [
            {"feature": feature_cols[i], "mi_score": round(float(mi[i]), 4), "rank": i + 1}
            for i in np.argsort(mi)[::-1]
        ]

        fig = go.Figure(
            go.Bar(
                x=[r["feature"] for r in results[:15]],
                y=[r["mi_score"] for r in results[:15]],
                marker_color=["#FF4D00" if i == 0 else "#2B2B2B" for i in range(len(results[:15]))],
                text=[str(round(r["mi_score"], 3)) for r in results[:15]],
                textposition="outside",
            )
        )
        fig.update_layout(
            title=f"Mutual Information vs {target_col}",
            xaxis_title="Feature",
            yaxis_title="MI Score",
            plot_bgcolor="#F5F5F5",
            paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=100, l=60, r=20),
            xaxis=dict(tickangle=-45),
        )

        top3 = [r["feature"] for r in results[:3]]
        comment = f"Le 3 feature con maggiore informazione mutua rispetto a '{target_col}' sono: {', '.join(top3)}."

        return {
            "target": target_col,
            "target_type": "classification" if is_class else "regression",
            "features": results,
            "charts": {"bar": _fig(fig)},
            "ai_comment": comment,
        }
    except Exception as e:
        return {"skipped": True, "error": str(e)}


# ── Clustering (KMeans) ─────────────────────────────────────────────────────


def _clustering(df, num_cols):
    if len(num_cols) < 2:
        return {"skipped": True, "reason": "Meno di 2 colonne numeriche"}

    try:
        cols = num_cols[:8]
        # ponytail: drop_nulls invece di fill_null per non distorcere varianza
        mat = df.select([
            pl.col(c).cast(pl.Float64) for c in cols
        ]).drop_nulls().to_numpy()
        if len(mat) < 20:
            return {"skipped": True, "reason": "Dati insufficienti"}

        mat_s = StandardScaler().fit_transform(mat)
        n_sample = min(len(mat_s), 5000)
        mat_s = mat_s[:n_sample]

        k_range = range(2, min(9, n_sample // 5 + 1))
        inertias = []
        silhouettes = []

        for k in k_range:
            km = KMeans(n_clusters=k, random_state=42, n_init=5, max_iter=100)
            labels = km.fit_predict(mat_s)
            inertias.append(float(km.inertia_))
            if k >= 2:
                sil = silhouette_score(mat_s, labels, sample_size=min(1000, len(mat_s)))
                silhouettes.append({"k": k, "silhouette": round(float(sil), 4)})

        best_k_sil = max(silhouettes, key=lambda x: x["silhouette"])["k"] if silhouettes else 2

        # Final clustering con best_k
        km_final = KMeans(n_clusters=best_k_sil, random_state=42, n_init=10, max_iter=300)
        labels_final = km_final.fit_predict(mat_s)
        cluster_sizes = {int(k): int((labels_final == k).sum()) for k in range(best_k_sil)}

        # Elbow chart
        k_list = list(k_range)
        fig_elbow = go.Figure()
        fig_elbow.add_trace(
            go.Scatter(
                x=k_list,
                y=inertias,
                mode="lines+markers",
                line=dict(color="#2B2B2B", width=2),
                marker=dict(color="#FF4D00", size=8),
            )
        )
        fig_elbow.update_layout(
            title="KMeans — Elbow Method (Inertia)",
            xaxis_title="K",
            yaxis_title="Inertia",
            plot_bgcolor="#F5F5F5",
            paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=50, l=60, r=20),
        )

        # Silhouette chart
        fig_sil = go.Figure(
            go.Bar(
                x=[s["k"] for s in silhouettes],
                y=[s["silhouette"] for s in silhouettes],
                marker_color=[
                    "#FF4D00" if s["k"] == best_k_sil else "#2B2B2B" for s in silhouettes
                ],
            )
        )
        fig_sil.update_layout(
            title="KMeans — Silhouette Score per K",
            xaxis_title="K",
            yaxis_title="Silhouette",
            plot_bgcolor="#F5F5F5",
            paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=50, l=60, r=20),
        )

        # PCA-based scatter dei cluster
        pca2 = PCA(n_components=2)
        coords = pca2.fit_transform(mat_s)
        colors = [
            "#FF4D00",
            "#2B2B2B",
            "#888888",
            "#FFAA00",
            "#003366",
            "#990000",
            "#004400",
            "#444444",
        ]
        fig_scatter = go.Figure()
        for k in range(best_k_sil):
            mask2 = labels_final == k
            fig_scatter.add_trace(
                go.Scatter(
                    x=coords[mask2, 0].tolist(),
                    y=coords[mask2, 1].tolist(),
                    mode="markers",
                    name=f"Cluster {k}",
                    marker=dict(color=colors[k % len(colors)], size=5, opacity=0.7),
                )
            )
        fig_scatter.update_layout(
            title=f"KMeans K={best_k_sil} — Proiezione PCA",
            xaxis_title="PC1",
            yaxis_title="PC2",
            plot_bgcolor="#F5F5F5",
            paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=50, l=60, r=20),
        )

        return {
            "best_k": best_k_sil,
            "silhouette_scores": silhouettes,
            "cluster_sizes": cluster_sizes,
            "charts": {
                "elbow": _fig(fig_elbow),
                "silhouette": _fig(fig_sil),
                "scatter": _fig(fig_scatter),
            },
            "ai_comment": f"La soluzione ottimale suggerita è K={best_k_sil} cluster (miglior silhouette score). "
            + "I cluster sono proiettati sullo spazio PC1×PC2.",
        }
    except Exception as e:
        return {"skipped": True, "error": str(e)}


# ── Anomaly Detection ────────────────────────────────────────────────────────


def _anomaly(df, num_cols):
    if len(num_cols) < 2:
        return {"skipped": True, "reason": "Meno di 2 colonne numeriche"}

    try:
        cols = num_cols[:10]
        # ponytail: drop_nulls invece di fill_null
        mat = df.select([
            pl.col(c).cast(pl.Float64) for c in cols
        ]).drop_nulls().to_numpy()
        if len(mat) < 21:
            return {"skipped": True, "reason": "Dati insufficienti"}

        mat_s = StandardScaler().fit_transform(mat)
        n_sample = min(len(mat_s), 10_000)
        mat_s = mat_s[:n_sample]

        # Isolation Forest
        iso = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
        iso_pred = iso.fit_predict(mat_s)  # -1 = anomalia
        iso_scores = iso.score_samples(mat_s)

        # LOF
        lof = LocalOutlierFactor(n_neighbors=20, contamination=0.05)
        lof_pred = lof.fit_predict(mat_s)

        # Consensus
        consensus = (iso_pred == -1) & (lof_pred == -1)
        n_iso = int((iso_pred == -1).sum())
        n_lof = int((lof_pred == -1).sum())
        n_cons = int(consensus.sum())
        n_total = len(mat_s)

        # Anomaly score distribution
        fig_score = go.Figure()
        normal_scores = iso_scores[iso_pred == 1].tolist()
        anomaly_scores = iso_scores[iso_pred == -1].tolist()
        if normal_scores:
            fig_score.add_trace(
                go.Histogram(
                    x=normal_scores, name="Normale", marker_color="#2B2B2B", opacity=0.7, nbinsx=30
                )
            )
        if anomaly_scores:
            fig_score.add_trace(
                go.Histogram(
                    x=anomaly_scores,
                    name="Anomalia",
                    marker_color="#FF4D00",
                    opacity=0.8,
                    nbinsx=20,
                )
            )
        fig_score.update_layout(
            title="Isolation Forest — Distribuzione anomaly score",
            xaxis_title="Score",
            yaxis_title="Frequenza",
            barmode="overlay",
            plot_bgcolor="#F5F5F5",
            paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=50, l=60, r=20),
        )

        return {
            "n_observations": n_total,
            "isolation_forest": {"n_anomalies": n_iso, "pct": round(n_iso / n_total * 100, 2)},
            "lof": {"n_anomalies": n_lof, "pct": round(n_lof / n_total * 100, 2)},
            "consensus": {"n_anomalies": n_cons, "pct": round(n_cons / n_total * 100, 2)},
            "features_used": cols,
            "charts": {"score_distribution": _fig(fig_score)},
            "ai_comment": (
                f"Rilevate {n_iso} anomalie con Isolation Forest ({round(n_iso / n_total * 100, 1)}%) "
                f"e {n_lof} con LOF. "
            )
            + f"Consenso tra i due metodi: {n_cons} osservazioni anomale "
            f"({round(n_cons / n_total * 100, 1)}%).",
        }
    except Exception as e:
        return {"skipped": True, "error": str(e)}
