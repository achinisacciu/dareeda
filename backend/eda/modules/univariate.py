import polars as pl
import plotly.graph_objects as go
import plotly.express as px
import json, math
from scipy import stats as scipy_stats
import numpy as np


def _fig(fig: go.Figure) -> dict:
    return json.loads(fig.to_json())


def run(df: pl.DataFrame, df_full: pl.DataFrame, semantic_types: dict, groups: dict) -> dict:
    results = {}
    for col in df.columns:
        stype = semantic_types.get(col, "unknown")
        try:
            if stype == "numeric_continuous":
                results[col] = _numeric_continuous(df[col], col)
            elif stype == "numeric_discrete":
                results[col] = _numeric_discrete(df[col], col)
            elif stype in ("categorical_nominal", "categorical_ordinal"):
                results[col] = _categorical(df[col], col, stype)
            elif stype == "boolean":
                results[col] = _boolean(df[col], col)
            elif stype == "datetime":
                results[col] = _datetime(df[col], col)
            elif stype == "text":
                results[col] = _text(df[col], col)
            elif stype == "id":
                results[col] = _id_col(df[col], col)
            elif stype == "geographic":
                results[col] = _geographic(df[col], col)
            else:
                results[col] = {"semantic_type": stype, "skipped": True}
        except Exception as e:
            results[col] = {"semantic_type": stype, "error": str(e)}
    return results


def _plot_indices(n: int, max_points: int = 1500) -> np.ndarray:
    if n <= max_points:
        return np.arange(n)
    return np.linspace(0, n - 1, max_points, dtype=int)


def _qq_confidence_band(n: int, slope: float, intercept: float) -> tuple[np.ndarray, np.ndarray]:
    ranks = np.arange(1, n + 1)
    lower_u = scipy_stats.beta.ppf(0.025, ranks, n - ranks + 1)
    upper_u = scipy_stats.beta.ppf(0.975, ranks, n - ranks + 1)
    lower_u = np.clip(lower_u, 1e-6, 1 - 1e-6)
    upper_u = np.clip(upper_u, 1e-6, 1 - 1e-6)
    lower = scipy_stats.norm.ppf(lower_u) * slope + intercept
    upper = scipy_stats.norm.ppf(upper_u) * slope + intercept
    return lower, upper


# ── Numerico continuo ─────────────────────────────────────────────────────────

def _numeric_continuous(s: pl.Series, col: str) -> dict:
    valid = s.drop_nulls().cast(pl.Float64)
    arr   = valid.to_numpy()
    n     = len(arr)

    if n == 0:
        return {"semantic_type": "numeric_continuous", "error": "Nessun valore valido"}

    q1, q3   = float(np.percentile(arr, 25)), float(np.percentile(arr, 75))
    iqr      = q3 - q1
    low_b    = q1 - 1.5 * iqr
    high_b   = q3 + 1.5 * iqr
    n_out    = int(np.sum((arr < low_b) | (arr > high_b)))
    skew     = float(scipy_stats.skew(arr))
    kurt     = float(scipy_stats.kurtosis(arr))
    cv       = float(np.std(arr) / np.mean(arr)) if np.mean(arr) != 0 else None

    # Normalità
    if n <= 5000:
        stat_norm, p_norm = scipy_stats.shapiro(arr[:5000])
        test_name = "Shapiro-Wilk"
    else:
        stat_norm, p_norm = scipy_stats.jarque_bera(arr)
        test_name = "Jarque-Bera"
    norm_flag = "normale" if p_norm > 0.05 else "non normale"

    stats = {
        "count":       n,
        "missing_pct": round(s.null_count() / len(s) * 100, 2),
        "mean":        round(float(np.mean(arr)), 4),
        "median":      round(float(np.median(arr)), 4),
        "std":         round(float(np.std(arr)), 4),
        "cv":          round(cv, 4) if cv is not None else None,
        "min":         round(float(arr.min()), 4),
        "p1":          round(float(np.percentile(arr, 1)), 4),
        "p5":          round(float(np.percentile(arr, 5)), 4),
        "q1":          round(q1, 4),
        "q3":          round(q3, 4),
        "p95":         round(float(np.percentile(arr, 95)), 4),
        "p99":         round(float(np.percentile(arr, 99)), 4),
        "max":         round(float(arr.max()), 4),
        "iqr":         round(iqr, 4),
        "skewness":    round(skew, 4),
        "kurtosis":    round(kurt, 4),
        "outlier_iqr_n":   n_out,
        "outlier_iqr_pct": round(n_out / n * 100, 2),
        "normality_test":  test_name,
        "normality_stat":  round(float(stat_norm), 4),
        "normality_pval":  round(float(p_norm), 4),
        "normality_flag":  norm_flag,
    }

    bins = min(50, max(10, n // 100))

    # Histogram + KDE
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=arr.tolist(), nbinsx=bins,
        name="Frequenza", marker_color="#59ADF7", opacity=0.82,
    ))
    if n > 1 and float(np.std(arr)) > 0:
        kde_x = np.linspace(float(arr.min()), float(arr.max()), 240)
        kde = scipy_stats.gaussian_kde(arr)
        data_range = float(arr.max()) - float(arr.min())
        bin_width = data_range / bins if data_range > 0 else 1.0
        kde_y = kde(kde_x) * n * bin_width
        fig_hist.add_trace(go.Scatter(
            x=kde_x.tolist(),
            y=kde_y.tolist(),
            mode="lines",
            name="KDE",
            line=dict(color="#E4002B", width=3),
            yaxis="y",
        ))
    fig_hist.update_layout(
        title=f"Distribuzione — {col}",
        xaxis_title=col, yaxis_title="Frequenza",
        plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=50, l=60, r=20),
    )

    # Box plot
    fig_box = go.Figure(go.Box(
        y=arr.tolist(), name=col,
        marker_color="#FF4D00", line_color="#000000",
        boxmean="sd",
    ))
    fig_box.update_layout(
        title=f"Box Plot — {col}",
        yaxis_title=col,
        plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=50, l=60, r=20),
    )

    # QQ Plot
    qq = scipy_stats.probplot(arr, dist="norm")
    qq_theoretical = np.asarray(qq[0][0], dtype=float)
    qq_sample = np.asarray(qq[0][1], dtype=float)
    qq_idx = _plot_indices(len(qq_theoretical))
    qq_x = qq_theoretical[qq_idx]
    qq_y = qq_sample[qq_idx]
    slope, intercept = float(qq[1][0]), float(qq[1][1])
    qq_lower, qq_upper = _qq_confidence_band(len(qq_theoretical), slope, intercept)
    qq_lower = qq_lower[qq_idx]
    qq_upper = qq_upper[qq_idx]
    fig_qq = go.Figure()
    fig_qq.add_trace(go.Scatter(
        x=qq_x.tolist(),
        y=qq_lower.tolist(),
        mode="lines",
        line=dict(color="rgba(89,173,247,0)"),
        showlegend=False,
        hoverinfo="skip",
    ))
    fig_qq.add_trace(go.Scatter(
        x=qq_x.tolist(),
        y=qq_upper.tolist(),
        mode="lines",
        fill="tonexty",
        fillcolor="rgba(89,173,247,0.18)",
        line=dict(color="rgba(89,173,247,0)"),
        name="Banda 95%",
        hoverinfo="skip",
    ))
    fig_qq.add_trace(go.Scatter(
        x=qq_x.tolist(),
        y=qq_y.tolist(),
        mode="markers",
        marker=dict(color="#1B272F", size=4),
        name="Dati",
    ))
    line_x = [float(qq_x.min()), float(qq_x.max())]
    fig_qq.add_trace(go.Scatter(
        x=line_x,
        y=[slope * x + intercept for x in line_x],
        mode="lines",
        line=dict(color="#E4002B", width=2),
        name="Linea teorica",
    ))
    fig_qq.update_layout(
        title=f"QQ Plot — {col}",
        xaxis_title="Quantili teorici", yaxis_title="Quantili campione",
        plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=50, l=60, r=20),
    )

    sorted_arr = np.sort(arr)
    ecdf_y = np.arange(1, n + 1) / n
    ecdf_idx = _plot_indices(n, max_points=2000)
    fig_ecdf = go.Figure()
    fig_ecdf.add_trace(go.Scatter(
        x=sorted_arr[ecdf_idx].tolist(),
        y=ecdf_y[ecdf_idx].tolist(),
        mode="lines",
        line=dict(color="#0904AE", width=3, shape="hv"),
        name="ECDF",
    ))
    fig_ecdf.update_layout(
        title=f"ECDF — {col}",
        xaxis_title=col,
        yaxis_title="Frequenza cumulata relativa",
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=50, l=60, r=20),
        yaxis=dict(range=[0, 1]),
    )

    comment = _comment_numeric(skew, kurt, n_out, n, norm_flag, cv)
    suggestions = _suggest_numeric(skew, n_out, n, cv)

    return {
        "semantic_type": "numeric_continuous",
        "stats":         stats,
        "charts": {
            "histogram": _fig(fig_hist),
            "boxplot":   _fig(fig_box),
            "qqplot":    _fig(fig_qq),
            "ecdf":      _fig(fig_ecdf),
        },
        "ai_comment":  comment,
        "suggestions": suggestions,
    }


def _comment_numeric(skew, kurt, n_out, n, norm_flag, cv) -> str:
    parts = []
    if abs(skew) < 0.5:
        parts.append("La distribuzione è approssimativamente simmetrica.")
    elif skew > 0.5:
        parts.append(f"La distribuzione presenta asimmetria positiva (skewness={skew:.2f}): coda destra pronunciata.")
    else:
        parts.append(f"La distribuzione presenta asimmetria negativa (skewness={skew:.2f}): coda sinistra pronunciata.")
    if kurt > 3:
        parts.append("Code pesanti rilevate (leptocurtica): probabile presenza di outlier estremi.")
    if n_out > 0:
        parts.append(f"Rilevati {n_out} outlier ({round(n_out/n*100,1)}%) secondo il metodo IQR.")
    if norm_flag == "non normale":
        parts.append("Il test di normalità rigetta l'ipotesi di distribuzione normale.")
    return " ".join(parts)


def _suggest_numeric(skew, n_out, n, cv) -> list[dict]:
    suggestions = []
    if abs(skew) > 1:
        suggestions.append({"motivo": f"Skewness elevata ({skew:.2f})", "trasformazione": "Log o Box-Cox", "priorita": "alta"})
    if n_out > n * 0.05:
        suggestions.append({"motivo": "Outlier >5% dei dati", "trasformazione": "Winsorization (P1-P99)", "priorita": "alta"})
    if cv is not None and cv > 1:
        suggestions.append({"motivo": "Alta variabilità relativa (CV>1)", "trasformazione": "StandardScaler o RobustScaler", "priorita": "media"})
    return suggestions


# ── Numerico discreto ─────────────────────────────────────────────────────────

def _numeric_discrete(s: pl.Series, col: str) -> dict:
    valid    = s.drop_nulls()
    n        = len(valid)
    vc       = valid.value_counts(sort=True)
    mode_val = str(vc[col][0]) if n > 0 else None
    imbalance = round(float(vc["count"][0]) / n * 100, 2) if n > 0 else 0.0

    freqs = [{"level": str(vc[col][i]), "count": int(vc["count"][i]),
               "pct": round(float(vc["count"][i]) / n * 100, 2)} for i in range(min(30, len(vc)))]

    fig = go.Figure(go.Bar(
        x=[f["level"] for f in freqs], y=[f["count"] for f in freqs],
        marker_color="#1B272F", text=[f'{f["pct"]}%' for f in freqs], textposition="outside",
    ))
    fig.update_layout(
        title=f"Distribuzione discreta — {col}",
        xaxis_title=col, yaxis_title="Frequenza",
        plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=60, l=60, r=20),
    )

    return {
        "semantic_type": "numeric_discrete",
        "stats": {
            "count": n, "missing_pct": round(s.null_count()/len(s)*100, 2),
            "n_unique": int(valid.n_unique()), "mode": mode_val,
            "min": int(valid.min()), "max": int(valid.max()),
            "imbalance_ratio": imbalance,
        },
        "frequencies": freqs,
        "charts": {"bar": _fig(fig)},
        "ai_comment": f"Variabile discreta con {valid.n_unique()} livelli distinti. Valore dominante: {mode_val} ({imbalance:.1f}%).",
    }


# ── Categorico ────────────────────────────────────────────────────────────────

def _categorical(s: pl.Series, col: str, stype: str) -> dict:
    valid = s.drop_nulls().cast(pl.String)
    n     = len(valid)
    if n == 0:
        return {"semantic_type": stype, "error": "Nessun valore valido"}

    vc        = valid.value_counts(sort=True)
    n_unique  = int(valid.n_unique())
    card_r    = round(n_unique / n * 100, 2)
    mode_val  = str(vc[col][0])
    mode_pct  = round(float(vc["count"][0]) / n * 100, 2)
    dom_pct   = mode_pct

    # Entropia normalizzata
    counts    = vc["count"].to_numpy().astype(float)
    probs     = counts / counts.sum()
    entropy   = float(-np.sum(probs * np.log2(probs + 1e-10)))
    max_entr  = math.log2(n_unique) if n_unique > 1 else 1
    norm_entr = round(entropy / max_entr, 3) if max_entr > 0 else 0.0
    imbalance = round(float(vc["count"][0]) / float(vc["count"][-1]) if len(vc) > 1 else 1.0, 2)

    top_n  = min(15, len(vc))
    labels = [str(vc[col][i]) for i in range(top_n)]
    counts_top = [int(vc["count"][i]) for i in range(top_n)]
    pcts_top   = [round(c / n * 100, 2) for c in counts_top]

    freqs = [{"category": labels[i], "count": counts_top[i], "pct": pcts_top[i],
               "cum_pct": round(sum(pcts_top[:i+1]), 2)} for i in range(top_n)]

    fig = go.Figure(go.Bar(
        x=labels, y=counts_top,
        marker_color=["#E4002B" if i == 0 else "#1B272F" for i in range(top_n)],
        text=[f'{p}%' for p in pcts_top], textposition="outside",
    ))
    fig.update_layout(
        title=f"Top {top_n} categorie — {col}",
        xaxis_title=col, yaxis_title="Frequenza",
        plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=100, l=60, r=20),
        xaxis=dict(tickangle=-45),
    )

    rare = [str(vc[col][i]) for i in range(len(vc)) if float(vc["count"][i]) / n * 100 < 1]
    comment = _comment_categorical(n_unique, card_r, imbalance, len(rare))

    charts = {"bar": _fig(fig)}

    if stype == "categorical_ordinal":
        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(
            x=labels,
            y=[round(p / 100, 4) for p in np.cumsum(pcts_top)],
            mode="lines+markers",
            line=dict(color="#0904AE", width=3, shape="hv"),
            marker=dict(size=7, color="#0904AE"),
            name="Freq. rel. cumulata",
        ))
        fig_cum.update_layout(
            title=f"Frequenze relative cumulate — {col}",
            xaxis_title=col,
            yaxis_title="Quota cumulata",
            plot_bgcolor="#F5F5F5",
            paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=100, l=60, r=20),
            xaxis=dict(tickangle=-45),
            yaxis=dict(range=[0, 1]),
        )
        charts["cumulative_relative"] = _fig(fig_cum)

    if stype == "categorical_nominal":
        cum_pct = np.cumsum(pcts_top)
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=labels,
            y=counts_top,
            marker_color="#1B272F",
            text=[f"{p}%" for p in pcts_top],
            textposition="outside",
            name="Frequenza",
        ))
        fig_pareto.add_trace(go.Scatter(
            x=labels,
            y=cum_pct.tolist(),
            mode="lines+markers",
            line=dict(color="#E4002B", width=3),
            marker=dict(size=7, color="#E4002B"),
            name="Cumulata %",
            yaxis="y2",
        ))
        fig_pareto.update_layout(
            title=f"Pareto — {col}",
            xaxis_title=col,
            yaxis=dict(title="Frequenza"),
            yaxis2=dict(title="% cumulata", overlaying="y", side="right", range=[0, 100]),
            plot_bgcolor="#F5F5F5",
            paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=100, l=60, r=60),
            xaxis=dict(tickangle=-45),
        )

        fig_treemap = go.Figure(go.Treemap(
            labels=labels,
            parents=[""] * len(labels),
            values=counts_top,
            marker=dict(colors=["#59ADF7", "#0904AE", "#E4002B", "#112F44", "#37424A"] * 4),
            textinfo="label+percent entry",
        ))
        fig_treemap.update_layout(
            title=f"Treemap — {col}",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=20, l=20, r=20),
        )

        charts["pareto"] = _fig(fig_pareto)
        charts["treemap"] = _fig(fig_treemap)

    return {
        "semantic_type": stype,
        "stats": {
            "count": n, "missing_pct": round(s.null_count()/len(s)*100, 2),
            "n_unique": n_unique, "cardinality_ratio": card_r,
            "mode": mode_val, "mode_pct": mode_pct,
            "normalized_entropy": norm_entr,
            "imbalance_ratio": imbalance, "dominant_class_pct": dom_pct,
            "n_rare_categories": len(rare),
        },
        "frequencies": freqs,
        "charts": charts,
        "ai_comment": comment,
        "flags": {
            "high_cardinality": card_r > 50,
            "rare_categories":  len(rare) > 0,
            "possible_quasi_id": card_r > 90,
        },
    }


def _comment_categorical(n_unq, card_r, imbalance, n_rare) -> str:
    parts = []
    if card_r > 90:
        parts.append(f"Alta cardinalità ({card_r:.1f}%): questa colonna potrebbe essere un quasi-ID.")
    elif card_r > 50:
        parts.append(f"Cardinalità elevata ({n_unq} categorie). Valutare raggruppamento o encoding a cardinalità ridotta.")
    else:
        parts.append(f"Variabile categorica con {n_unq} categorie distinte.")
    if imbalance > 10:
        parts.append(f"Forte sbilanciamento tra le classi (ratio {imbalance:.1f}x): la classe dominante è molto più frequente.")
    if n_rare > 0:
        parts.append(f"Presenti {n_rare} categorie rare (<1% dei dati). Valutare accorpamento in categoria 'Altro'.")
    return " ".join(parts)


# ── Booleano ──────────────────────────────────────────────────────────────────

def _boolean(s: pl.Series, col: str) -> dict:
    valid  = s.drop_nulls().cast(pl.String).str.to_lowercase()
    n      = len(valid)
    true_vals  = {"true","1","yes","si","t","y"}
    false_vals = {"false","0","no","f","n"}
    n_true  = int(valid.is_in(list(true_vals)).sum())
    n_false = int(valid.is_in(list(false_vals)).sum())
    if n_true == 0 and n_false == 0:
        # fallback: maggiore vs minore frequenza
        vc = valid.value_counts(sort=True)
        n_true  = int(vc["count"][0]) if len(vc) > 0 else 0
        n_false = int(vc["count"][1]) if len(vc) > 1 else 0
    pct_true  = round(n_true  / n * 100, 2) if n > 0 else 0.0
    pct_false = round(n_false / n * 100, 2) if n > 0 else 0.0
    imbalance = round(max(pct_true, pct_false) / min(pct_true, pct_false), 2) if min(pct_true, pct_false) > 0 else None

    fig = go.Figure(go.Bar(
        x=["True / Sì", "False / No"], y=[n_true, n_false],
        marker_color=["#E4002B", "#1B272F"],
        text=[f'{pct_true}%', f'{pct_false}%'], textposition="outside",
    ))
    fig.update_layout(
        title=f"Distribuzione booleana — {col}",
        plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=50, l=60, r=20),
    )

    fig_donut = go.Figure(go.Pie(
        labels=["True / Sì", "False / No"],
        values=[n_true, n_false],
        hole=0.58,
        marker=dict(colors=["#E4002B", "#59ADF7"]),
        sort=False,
        textinfo="label+percent",
    ))
    fig_donut.update_layout(
        title=f"Anello booleano — {col}",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=20, l=20, r=20),
        showlegend=False,
    )

    return {
        "semantic_type": "boolean",
        "stats": {
            "count": n, "missing_pct": round(s.null_count()/len(s)*100, 2),
            "true_count": n_true, "false_count": n_false,
            "true_pct": pct_true, "false_pct": pct_false,
            "imbalance_ratio": imbalance,
        },
        "charts": {
            "bar": _fig(fig),
            "donut": _fig(fig_donut),
        },
        "ai_comment": f"Variabile booleana. Rapporto True/False: {pct_true:.1f}% vs {pct_false:.1f}%." +
                      (" Sbilanciamento significativo rilevato." if imbalance and imbalance > 3 else ""),
    }


# ── Datetime ──────────────────────────────────────────────────────────────────

def _datetime(s: pl.Series, col: str) -> dict:
    valid = s.drop_nulls()
    n     = len(valid)
    if n == 0:
        return {"semantic_type": "datetime", "error": "Nessun valore valido"}

    try:
        if valid.dtype not in (pl.Date, pl.Datetime):
            valid = valid.cast(pl.String).str.to_datetime(strict=False).drop_nulls()
        dt_valid = valid.cast(pl.Datetime)
        min_dt = str(dt_valid.min())
        max_dt = str(dt_valid.max())
        range_days = (dt_valid.max() - dt_valid.min()).days if hasattr((dt_valid.max() - dt_valid.min()), 'days') else None

        # Freq per anno
        years = dt_valid.dt.year().alias("year").value_counts(sort=True).sort("year")
        fig_year = go.Figure(go.Bar(
            x=years["year"].cast(pl.String).to_list(),
            y=years["count"].to_list(),
            marker_color="#2B2B2B",
        ))
        fig_year.update_layout(
            title=f"Osservazioni per anno — {col}",
            plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=50, l=60, r=20),
        )

        # Freq per mese
        months = dt_valid.dt.month().alias("month").value_counts(sort=False).sort("month")
        month_names = ["Gen","Feb","Mar","Apr","Mag","Giu","Lug","Ago","Set","Ott","Nov","Dic"]
        fig_month = go.Figure(go.Bar(
            x=[month_names[m-1] for m in months["month"].to_list()],
            y=months["count"].to_list(),
            marker_color="#FF4D00",
        ))
        fig_month.update_layout(
            title=f"Osservazioni per mese — {col}",
            plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
            font=dict(family="JetBrains Mono", size=11),
            margin=dict(t=50, b=50, l=60, r=20),
        )

        return {
            "semantic_type": "datetime",
            "stats": {
                "count": n, "missing_pct": round(s.null_count()/len(s)*100, 2),
                "min_date": min_dt, "max_date": max_dt,
                "range_days": range_days, "n_unique": int(dt_valid.n_unique()),
            },
            "charts": {"by_year": _fig(fig_year), "by_month": _fig(fig_month)},
            "ai_comment": f"Variabile temporale con range da {min_dt} a {max_dt} ({range_days} giorni). Verificare gap temporali e stagionalità.",
        }
    except Exception as e:
        return {"semantic_type": "datetime", "error": str(e)}


# ── Testo libero ──────────────────────────────────────────────────────────────

def _text(s: pl.Series, col: str) -> dict:
    valid    = s.drop_nulls().cast(pl.String)
    n        = len(valid)
    lengths  = valid.str.len_chars()
    avg_len  = round(float(lengths.mean()), 1) if n > 0 else 0.0
    med_len  = round(float(lengths.median()), 1) if n > 0 else 0.0
    p95_len  = round(float(lengths.quantile(0.95)), 1) if n > 0 else 0.0
    n_empty  = int((valid.str.strip_chars() == "").sum())

    fig = go.Figure(go.Histogram(
        x=lengths.to_list(), nbinsx=40,
        marker_color="#2B2B2B", opacity=0.85,
    ))
    fig.update_layout(
        title=f"Lunghezza testo — {col}",
        xaxis_title="N caratteri", yaxis_title="Frequenza",
        plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=50, l=60, r=20),
    )

    return {
        "semantic_type": "text",
        "stats": {
            "count": n, "missing_pct": round(s.null_count()/len(s)*100, 2),
            "n_unique": int(valid.n_unique()),
            "cardinality_ratio": round(valid.n_unique()/n*100, 2) if n > 0 else 0.0,
            "avg_length": avg_len, "median_length": med_len, "p95_length": p95_len,
            "empty_like_pct": round(n_empty/n*100, 2) if n > 0 else 0.0,
        },
        "charts": {"length_hist": _fig(fig)},
        "ai_comment": f"Colonna testuale. Lunghezza media {avg_len:.0f} caratteri, P95 {p95_len:.0f}. Richiedere pipeline NLP dedicata per analisi semantica.",
    }


# ── ID / quasi-ID ─────────────────────────────────────────────────────────────

def _id_col(s: pl.Series, col: str) -> dict:
    n         = len(s)
    n_unique  = int(s.drop_nulls().n_unique())
    uniq_r    = round(n_unique / n * 100, 2) if n > 0 else 0.0
    n_dup     = n - n_unique
    return {
        "semantic_type": "id",
        "stats": {
            "count": n, "missing_pct": round(s.null_count()/n*100, 2),
            "n_unique": n_unique, "unique_ratio": uniq_r, "duplicate_count": n_dup,
        },
        "ai_comment": f"Colonna identificativa ({uniq_r:.1f}% valori unici). Escludere dall'analisi statistica e dalla modellazione.",
        "action": "escludere",
    }


# ── Geografico ────────────────────────────────────────────────────────────────

def _geographic(s: pl.Series, col: str) -> dict:
    valid = s.drop_nulls()
    n     = len(valid)
    try:
        num = valid.cast(pl.Float64, strict=False).drop_nulls()
        return {
            "semantic_type": "geographic",
            "stats": {
                "count": n, "missing_pct": round(s.null_count()/len(s)*100, 2),
                "min": round(float(num.min()), 5), "max": round(float(num.max()), 5),
                "n_unique": int(num.n_unique()),
                "out_of_range_count": int(((num < -180) | (num > 180)).sum()),
            },
            "ai_comment": f"Colonna geografica. Range [{float(num.min()):.4f}, {float(num.max()):.4f}]. Verificare coordinate fuori range.",
        }
    except Exception:
        return {"semantic_type": "geographic", "error": "Conversione numerica fallita"}

