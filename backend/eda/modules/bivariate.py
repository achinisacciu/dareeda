import polars as pl
import plotly.graph_objects as go
import numpy as np, json
from scipy import stats as sp


def _fig(f): return json.loads(f.to_json())


def run(df, df_full, semantic_types, groups):
    num_cols = groups.get("numeric_continuous", []) + groups.get("numeric_discrete", [])
    cat_cols = groups.get("categorical_nominal", []) + groups.get("categorical_ordinal", [])
    return {
        "num_num":    _num_num(df, num_cols),
        "num_cat":    _num_cat(df, num_cols, cat_cols),
        "cat_cat":    _cat_cat(df, cat_cols),
    }


def _num_num(df, num_cols):
    if len(num_cols) < 2:
        return {"skipped": True, "reason": "Meno di 2 colonne numeriche"}

    cols = num_cols[:20]  # max 20
    mat_pearson  = {}
    mat_spearman = {}
    pairs = []

    for i, a in enumerate(cols):
        for b in cols[i+1:]:
            va = df[a].drop_nulls().cast(pl.Float64)
            vb = df[b].drop_nulls().cast(pl.Float64)
            n_min = min(len(va), len(vb))
            if n_min < 10:
                continue
            arr_a = va[:n_min].to_numpy()
            arr_b = vb[:n_min].to_numpy()
            pr, pp = sp.pearsonr(arr_a, arr_b)
            sr, sp_ = sp.spearmanr(arr_a, arr_b)
            pairs.append({
                "var_a": a, "var_b": b,
                "pearson_r":    round(float(pr), 4),
                "spearman_rho": round(float(sr), 4),
                "n":            n_min,
                "note": "Alta correlazione" if abs(pr) > 0.7 else "",
            })

    pairs.sort(key=lambda x: abs(x["pearson_r"]), reverse=True)

    # Correlation heatmap
    arr = np.zeros((len(cols), len(cols)))
    idx = {c: i for i, c in enumerate(cols)}
    for p in pairs:
        i, j = idx[p["var_a"]], idx[p["var_b"]]
        arr[i][j] = arr[j][i] = p["pearson_r"]
    for i in range(len(cols)):
        arr[i][i] = 1.0

    fig_hm = go.Figure(go.Heatmap(
        z=arr.tolist(), x=cols, y=cols,
        colorscale=[[0,"#2B2B2B"],[0.5,"#FFFFFF"],[1,"#FF4D00"]],
        zmid=0, zmin=-1, zmax=1,
        text=[[f"{arr[i][j]:.2f}" for j in range(len(cols))] for i in range(len(cols))],
        texttemplate="%{text}", showscale=True,
    ))
    fig_hm.update_layout(
        title="Matrice di correlazione (Pearson)",
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=10),
        margin=dict(t=50, b=100, l=100, r=20),
        xaxis=dict(tickangle=-45),
    )

    # Top-5 scatter
    scatters = {}
    for p in pairs[:5]:
        a, b = p["var_a"], p["var_b"]
        arr_a = df[a].drop_nulls().cast(pl.Float64).to_numpy()
        arr_b = df[b].drop_nulls().cast(pl.Float64).to_numpy()
        n = min(len(arr_a), len(arr_b), 2000)
        fig_sc = go.Figure()
        fig_sc.add_trace(go.Scatter(x=arr_a[:n].tolist(), y=arr_b[:n].tolist(),
                                    mode="markers", marker=dict(color="#2B2B2B", size=4, opacity=0.6)))
        m, q = np.polyfit(arr_a[:n], arr_b[:n], 1)
        xr = [float(arr_a[:n].min()), float(arr_a[:n].max())]
        fig_sc.add_trace(go.Scatter(x=xr, y=[m*x+q for x in xr], mode="lines",
                                    line=dict(color="#FF4D00", width=2), name="Trend"))
        fig_sc.update_layout(
            title=f"Scatter: {a} × {b}  (r={p['pearson_r']})",
            xaxis_title=a, yaxis_title=b,
            plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=50, l=60, r=20),
            showlegend=False,
        )
        scatters[f"{a}_x_{b}"] = _fig(fig_sc)

    comment = _comment_num_num(pairs)
    return {
        "pairs":   pairs[:30],
        "charts": {"correlation_heatmap": _fig(fig_hm), "scatters": scatters},
        "ai_comment": comment,
    }


def _comment_num_num(pairs):
    high = [p for p in pairs if abs(p["pearson_r"]) > 0.7]
    multi = [p for p in pairs if abs(p["pearson_r"]) > 0.85]
    parts = []
    if not pairs:
        return "Analisi bivariata numerica non disponibile (meno di 2 colonne)."
    if high:
        top = high[0]
        parts.append(f"La coppia con correlazione più elevata è {top['var_a']} × {top['var_b']} (r={top['pearson_r']}).")
    if multi:
        parts.append(f"Rilevata potenziale multicollinearità in {len(multi)} coppie (|r|>0.85). Valutare rimozione di feature ridondanti.")
    if not high:
        parts.append("Nessuna correlazione lineare forte rilevata tra le variabili numeriche.")
    return " ".join(parts)


def _num_cat(df, num_cols, cat_cols):
    if not num_cols or not cat_cols:
        return {"skipped": True, "reason": "Colonne numeriche o categoriche insufficienti"}

    results = []
    charts  = {}
    pairs_done = 0

    for num in num_cols[:5]:
        for cat in cat_cols[:3]:
            if pairs_done >= 9:
                break
            try:
                cat_vals = df[cat].drop_nulls().cast(pl.String)
                groups_list = cat_vals.unique().sort().to_list()[:8]
                if len(groups_list) < 2:
                    continue

                group_stats = []
                group_arrays = []
                for g in groups_list:
                    mask = df[cat].cast(pl.String) == g
                    vals = df[num].filter(mask).drop_nulls().cast(pl.Float64).to_numpy()
                    if len(vals) < 3:
                        continue
                    group_stats.append({
                        "group": g, "count": len(vals),
                        "mean": round(float(vals.mean()), 3),
                        "median": round(float(np.median(vals)), 3),
                        "std": round(float(vals.std()), 3),
                    })
                    group_arrays.append((g, vals))

                # Box plot per gruppo
                fig = go.Figure()
                for g, arr in group_arrays:
                    fig.add_trace(go.Box(y=arr.tolist(), name=str(g),
                                         marker_color="#FF4D00", line_color="#000000",
                                         boxmean=False))
                fig.update_layout(
                    title=f"{num} per {cat}",
                    yaxis_title=num,
                    plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
                    font=dict(family="JetBrains Mono", size=11),
                    margin=dict(t=50, b=60, l=60, r=20),
                )
                charts[f"{num}_by_{cat}"] = _fig(fig)
                results.append({"num": num, "cat": cat, "group_stats": group_stats})
                pairs_done += 1
            except Exception:
                pass

    return {"pairs": results, "charts": charts}


def _cat_cat(df, cat_cols):
    if len(cat_cols) < 2:
        return {"skipped": True, "reason": "Meno di 2 colonne categoriche"}

    results = []
    pairs_done = 0

    for i, a in enumerate(cat_cols[:6]):
        for b in cat_cols[i+1:6]:
            if pairs_done >= 6:
                break
            try:
                va = df[a].drop_nulls().cast(pl.String)
                vb = df[b].drop_nulls().cast(pl.String)
                n  = min(len(va), len(vb))
                arr_a = va[:n].to_numpy().astype(str)
                arr_b = vb[:n].to_numpy().astype(str)

                from sklearn.preprocessing import LabelEncoder
                le_a = LabelEncoder().fit_transform(arr_a)
                le_b = LabelEncoder().fit_transform(arr_b)

                ct = np.zeros((len(np.unique(le_a)), len(np.unique(le_b))), dtype=int)
                for x, y in zip(le_a, le_b):
                    ct[x][y] += 1

                chi2, p, dof, _ = sp.chi2_contingency(ct)
                n_obs = ct.sum()
                cramers_v = float(np.sqrt(chi2 / (n_obs * (min(ct.shape) - 1)))) if n_obs > 0 else 0.0

                results.append({
                    "var_a": a, "var_b": b,
                    "cramers_v":   round(cramers_v, 4),
                    "chi2_pvalue": round(float(p), 4),
                    "note":        "Associazione forte" if cramers_v > 0.3 else "",
                })
                pairs_done += 1
            except Exception:
                pass

    results.sort(key=lambda x: x["cramers_v"], reverse=True)
    return {"pairs": results}

