import json

import numpy as np
import plotly.graph_objects as go
import polars as pl
from scipy.stats import pearsonr
import numpy as np
import plotly.graph_objects as go
import polars as pl
from scipy.stats import pearsonr
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant


def _fig(f):
    return json.loads(f.to_json())


def _safe_cast_float(s: pl.Series) -> pl.Series:
    return s.cast(pl.Float64, strict=False)


def _variance_rank(df: pl.DataFrame, cols: list[str], top_n: int) -> list[str]:
    scores = []
    for c in cols:
        if c not in df.columns:
            continue
        vals = _safe_cast_float(df[c]).drop_nulls()
        if len(vals) < 2:
            continue
        v = vals.var()
        if v is None:
            continue
        scores.append((float(v), c))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scores[:top_n]]


def _high_correlation_pairs(
    df: pl.DataFrame, cols: list[str], limit: int = 20, min_n: int = 10
) -> list[dict]:
    """
    Insight correlazioni elevate tra un sottoinsieme di colonne.
    """
    cols = cols[:limit]
    if len(cols) < 2:
        return []

    pairs = []
    for i, a in enumerate(cols):
        # ponytail: subset comune drop_nulls per allineamento spaziale
        sub = df.select([pl.col(a).cast(pl.Float64)])
        if sub[a].null_count() == len(sub):
            continue
        for j in range(i + 1, len(cols)):
            b = cols[j]
            pair = df.select([
                pl.col(a).cast(pl.Float64),
                pl.col(b).cast(pl.Float64),
            ]).drop_nulls()
            if len(pair) < min_n:
                continue
            va = pair[a].to_numpy()
            vb = pair[b].to_numpy()
            r, _ = pearsonr(va, vb)
            rr = float(r)
            if abs(rr) > 0.7:
                pairs.append({
                    "var_a": a,
                    "var_b": b,
                    "correlation": round(rr, 4),
                    "flag": abs(rr) > 0.85,
                })

    pairs.sort(key=lambda p: abs(p["correlation"]), reverse=True)
    return pairs[:15]


def run(df, df_full, semantic_types, groups, context: dict | None = None):
    # ponytail: df_full non usato, mantenuto per compatibilità firma
    context = context or {}
    target = context.get("target")
    problem_type = context.get("problem_type")

    num_cols = groups.get("numeric_continuous", []) + groups.get("numeric_discrete", [])
    num_cols = [c for c in num_cols if c in df.columns]

    if len(num_cols) < 3:
        return {"skipped": True, "reason": "Meno di 3 colonne numeriche"}

    # Default selezione: top per varianza (calcolata sul campione usato dall'analisi)
    default_selection_3 = _variance_rank(df, num_cols, top_n=3)
    default_selection_4 = _variance_rank(df, num_cols, top_n=4)

    # Insight: coppie con correlazione elevata e diagnostica classica.
    ranking_cols = _variance_rank(df, num_cols, top_n=min(25, len(num_cols)))
    high_pairs = _high_correlation_pairs(df, ranking_cols, limit=20)
    correlation_global = _correlation_global(df, ranking_cols)
    pca = _pca(df, ranking_cols)
    vif_data = _calculate_vif(df, ranking_cols)
    
    ml_warnings = []
    if vif_data.get("high_vif"):
        ml_warnings.append({
            "type": "multicollinearity",
            "cols": vif_data["high_vif"],
            "action": "drop_one"
        })
        
    target_leakage = []
    if target and target in df.columns:
        target_leakage = _detect_target_leakage(df, ranking_cols, target)
        if target_leakage:
            ml_warnings.append({
                "type": "potential_target_leakage",
                "cols": [t["col"] for t in target_leakage],
                "action": "investigate"
            })
            
    ai_comment = _generate_ai_comment(pca, vif_data, target_leakage)

    return {
        "numeric_columns": num_cols,
        "default_selection_3": default_selection_3,
        "default_selection_4": default_selection_4,
        "high_correlation_pairs": high_pairs,
        "correlation_global": correlation_global,
        "pca": pca,
        "vif": vif_data.get("vif_scores"),
        "ml_warnings": ml_warnings,
        "target": target if target in df.columns else None,
        "problem_type": problem_type if problem_type in ("classification", "regression") else None,
        "ai_comment": ai_comment,
    }


def _correlation_global(df, num_cols):
    if len(num_cols) < 3:
        return {"skipped": True}

    cols = num_cols[:25]
    mat = np.eye(len(cols))

    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if i >= j:
                continue
            # ponytail: subset comune drop_nulls per allineamento spaziale
            pair = df.select([
                pl.col(a).cast(pl.Float64),
                pl.col(b).cast(pl.Float64),
            ]).drop_nulls()
            if len(pair) < 10:
                continue
            va = pair[a].to_numpy()
            vb = pair[b].to_numpy()
            r, _ = pearsonr(va, vb)
            mat[i][j] = mat[j][i] = float(r)

    fig = go.Figure(
        go.Heatmap(
            z=mat.tolist(),
            x=cols,
            y=cols,
            colorscale=[[0, "#2B2B2B"], [0.5, "#FFFFFF"], [1, "#FF4D00"]],
            zmid=0,
            zmin=-1,
            zmax=1,
            text=[[f"{mat[i][j]:.2f}" for j in range(len(cols))] for i in range(len(cols))],
            texttemplate="%{text}",
            showscale=True,
        )
    )
    fig.update_layout(
        title="Correlazione globale variabili numeriche",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=9),
        margin=dict(t=50, b=120, l=120, r=20),
        xaxis=dict(tickangle=-45),
    )

    high_pairs = []
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if i < j and abs(mat[i][j]) > 0.7:
                high_pairs.append({
                    "var_a": a,
                    "var_b": b,
                    "correlation": round(mat[i][j], 4),
                    "flag": abs(mat[i][j]) > 0.85,
                })

    return {"chart": _fig(fig), "high_correlation_pairs": high_pairs}


def _pca(df, num_cols):
    if len(num_cols) < 4:
        return {"skipped": True, "reason": "Meno di 4 colonne numeriche"}

    cols = num_cols[:20]
    try:
        mat = df.select([pl.col(c).cast(pl.Float64) for c in cols]).to_numpy()
        mask = ~np.isnan(mat).any(axis=1)
        mat = mat[mask]
        if len(mat) < 20:
            return {"skipped": True, "reason": "Dati insufficienti dopo rimozione NaN"}

        scaler = StandardScaler()
        mat_s = scaler.fit_transform(mat)

        n_comp = min(len(cols), 10, len(mat))
        pca = PCA(n_components=n_comp)
        scores = pca.fit_transform(mat_s)
        ev_r = pca.explained_variance_ratio_

        # Scree plot
        fig_scree = go.Figure()
        fig_scree.add_trace(
            go.Bar(
                x=[f"PC{i + 1}" for i in range(n_comp)],
                y=[round(float(e) * 100, 2) for e in ev_r],
                marker_color="#2B2B2B",
                name="Varianza spiegata",
            )
        )
        fig_scree.add_trace(
            go.Scatter(
                x=[f"PC{i + 1}" for i in range(n_comp)],
                y=[round(float(np.cumsum(ev_r)[i]) * 100, 2) for i in range(n_comp)],
                mode="lines+markers",
                line=dict(color="#FF4D00", width=2),
                name="Cumulativa",
            )
        )
        fig_scree.update_layout(
            title="PCA — Varianza spiegata per componente",
            yaxis_title="% Varianza",
            plot_bgcolor="#F5F5F5",
            paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=50, l=60, r=20),
        )

        # Scatter PC1 × PC2
        fig_scatter = go.Figure(
            go.Scatter(
                x=scores[:, 0].tolist(),
                y=scores[:, 1].tolist(),
                mode="markers",
                marker=dict(color="#2B2B2B", size=4, opacity=0.6),
            )
        )
        fig_scatter.update_layout(
            title="PCA — PC1 × PC2",
            xaxis_title="PC1",
            yaxis_title="PC2",
            plot_bgcolor="#F5F5F5",
            paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=50, l=60, r=20),
        )

        components = []
        for i in range(min(n_comp, 5)):
            loadings = pca.components_[i]
            top_idx = np.argsort(np.abs(loadings))[::-1][:3]
            components.append({
                "component": f"PC{i + 1}",
                "explained_variance": round(float(ev_r[i]) * 100, 2),
                "cumulative_variance": round(float(np.cumsum(ev_r)[i]) * 100, 2),
                "top_loading_variables": [cols[j] for j in top_idx],
            })

        return {
            "n_components_used": n_comp,
            "components": components,
            "charts": {"scree": _fig(fig_scree), "scatter_pc1_pc2": _fig(fig_scatter)},
            "ai_comment": [
                {
                    "role": "data_scientist",
                    "insight": (
                        f"Le prime 2 componenti spiegano il "
                        f"{round(float(np.cumsum(ev_r)[1]) * 100, 1)}% della varianza totale."
                    )
                }
            ],
        }
    except Exception as e:
        return {"skipped": True, "error": str(e)}

def _calculate_vif(df: pl.DataFrame, cols: list[str]) -> dict:
    if len(cols) < 2:
        return {"skipped": True}
        
    try:
        pdf = df.select([pl.col(c).cast(pl.Float64) for c in cols[:15]]).drop_nulls().to_pandas()
        if len(pdf) < 10:
            return {"skipped": True, "reason": "Dati insufficienti"}
            
        X = add_constant(pdf)
        vif_scores = []
        high_vif = []
        for i in range(1, X.shape[1]):
            v = variance_inflation_factor(X.values, i)
            col_name = X.columns[i]
            vif_scores.append({"feature": col_name, "vif": round(float(v), 2)})
            if v > 10.0:
                high_vif.append(col_name)
                
        return {"vif_scores": vif_scores, "high_vif": high_vif}
    except Exception as e:
        return {"skipped": True, "error": str(e)}

def _detect_target_leakage(df: pl.DataFrame, cols: list[str], target: str) -> list[dict]:
    leakage = []
    if df[target].dtype not in (pl.Float32, pl.Float64, pl.Int32, pl.Int64):
        return leakage
        
    for c in cols:
        if c == target:
            continue
        try:
            pair = df.select([pl.col(c).cast(pl.Float64), pl.col(target).cast(pl.Float64)]).drop_nulls()
            if len(pair) > 10:
                r, _ = pearsonr(pair[c].to_numpy(), pair[target].to_numpy())
                if abs(r) > 0.98:
                    leakage.append({"col": c, "correlation_with_target": round(float(r), 4)})
        except Exception:
            pass
    return leakage

def _generate_ai_comment(pca: dict, vif_data: dict, target_leakage: list[dict]) -> list[dict]:
    comments = []
    
    if target_leakage:
        cols = [t["col"] for t in target_leakage]
        comments.append({
            "role": "ml_engineer",
            "insight": f"Attenzione: potenziale target leakage rilevato per {', '.join(cols)} (|r|>0.98 col target). Verificare che non derivino dal target."
        })
        
    if vif_data.get("high_vif"):
        comments.append({
            "role": "ml_engineer",
            "insight": f"Rilevata alta multicollinearità (VIF > 10) nelle feature: {', '.join(vif_data['high_vif'][:3])}. Riconsiderare l'inclusione di queste variabili nei modelli lineari."
        })
        
    if pca.get("components"):
        pca_comment = pca.get("ai_comment", [])
        if pca_comment:
            comments.extend(pca_comment)
            
    if not comments:
        comments.append({
            "role": "data_scientist",
            "insight": "Nessuna anomalia multivariata di rilievo (leakage o multicollinearità). Dataset pronto per l'analisi delle componenti o ML."
        })
        
    return comments
