import json

import numpy as np
import plotly.graph_objects as go
import polars as pl


def _fig(f): return json.loads(f.to_json())


def run(df, df_full, semantic_types, groups):
    dt_cols  = groups.get("datetime", [])
    num_cols = groups.get("numeric_continuous", []) + groups.get("numeric_discrete", [])

    if not dt_cols or not num_cols:
        return {"active": False, "reason": "Nessuna colonna datetime o numerica rilevata"}

    ts_col  = dt_cols[0]
    # Priorità: se sono presenti feature derivate da date (es. *_year, *_month),
    # includile subito come "value columns" per renderle visibili in TimeSeries.
    derived_time_cols = [c for c in num_cols if c.endswith("_year") or c.endswith("_month")]
    val_cols = (derived_time_cols + [c for c in num_cols if c not in derived_time_cols])[:3]
    results  = {"active": True, "ts_column": ts_col, "analyses": {}}

    for val_col in val_cols:
        try:
            results["analyses"][val_col] = _analyze_series(df, ts_col, val_col)
        except Exception as e:
            results["analyses"][val_col] = {"error": str(e)}

    return results


def _analyze_series(df, ts_col, val_col):
    try:
        ts = df.select([pl.col(ts_col), pl.col(val_col)]).drop_nulls()
        ts = ts.with_columns(pl.col(ts_col).cast(pl.Datetime))
        ts = ts.sort(ts_col)
    except Exception as e:
        return {"error": f"Impossibile preparare la serie: {e}"}

    n = len(ts)
    if n < 10:
        return {"error": "Serie troppo corta (<10 osservazioni)"}

    dates = ts[ts_col].to_list()
    vals  = ts[val_col].cast(pl.Float64).to_numpy()
    min_dt = str(ts[ts_col].min())
    max_dt = str(ts[ts_col].max())

    # Line chart
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=[str(d) for d in dates], y=vals.tolist(),
        mode="lines", line=dict(color="#2B2B2B", width=1.5), name=val_col,
    ))
    # Rolling mean 10%
    w = max(3, n // 10)
    rolling = np.convolve(vals, np.ones(w)/w, mode="valid")
    fig_line.add_trace(go.Scatter(
        x=[str(d) for d in dates[w-1:]], y=rolling.tolist(),
        mode="lines", line=dict(color="#FF4D00", width=2, dash="dash"), name=f"Media mobile ({w})",
    ))
    fig_line.update_layout(
        title=f"Serie temporale — {val_col}",
        xaxis_title="Data", yaxis_title=val_col,
        plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=60, l=60, r=20),
    )

    # Stazionarietà (ADF)
    stationarity = _adf_test(vals)

    # ACF/PACF semplificato
    acf_vals = _acf(vals, max_lag=min(40, n//3))

    fig_acf = go.Figure()
    lags = list(range(len(acf_vals)))
    fig_acf.add_trace(go.Bar(x=lags, y=acf_vals, marker_color="#2B2B2B", name="ACF"))
    conf = 1.96 / np.sqrt(n)
    fig_acf.add_hline(y=conf,  line=dict(color="#FF4D00", dash="dash"))
    fig_acf.add_hline(y=-conf, line=dict(color="#FF4D00", dash="dash"))
    fig_acf.update_layout(
        title=f"Autocorrelazione (ACF) — {val_col}",
        xaxis_title="Lag", yaxis_title="ACF",
        plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=50, l=60, r=20),
    )

    comment = _ts_comment(stationarity, acf_vals, val_col)

    return {
        "metadata": {
            "n_observations": n,
            "min_date": min_dt,
            "max_date": max_dt,
        },
        "stationarity": stationarity,
        "acf": acf_vals[:20],
        "charts": {"line": _fig(fig_line), "acf": _fig(fig_acf)},
        "ai_comment": comment,
    }


def _adf_test(arr):
    try:
        from statsmodels.tsa.stattools import adfuller
        r = adfuller(arr, autolag="AIC")
        return {
            "test": "ADF",
            "statistic": round(float(r[0]), 4),
            "pvalue":    round(float(r[1]), 4),
            "decision":  "stazionaria" if r[1] < 0.05 else "non stazionaria",
        }
    except Exception as e:
        return {"test": "ADF", "error": str(e)}


def _acf(arr, max_lag=40):
    n    = len(arr)
    mean = arr.mean()
    denom = np.sum((arr - mean)**2)
    if denom == 0:
        return [0.0] * max_lag
    acf_vals = []
    for k in range(max_lag):
        cov = np.sum((arr[:n-k] - mean) * (arr[k:] - mean))
        acf_vals.append(round(float(cov / denom), 4))
    return acf_vals


def _ts_comment(stationarity, acf_vals, col):
    parts = []
    if "decision" in stationarity:
        d = stationarity["decision"]
        p = stationarity.get("pvalue", "N/A")
        parts.append(f"Il test ADF indica che la serie '{col}' è {d} (p={p}).")
        if d == "non stazionaria":
            parts.append("Considerare differenziazione prima della modellazione.")
    significant_lags = [i for i, v in enumerate(acf_vals[1:], 1) if abs(v) > 0.2]
    if significant_lags:
        parts.append(f"Autocorrelazione significativa ai lag: {significant_lags[:5]}.")
    return " ".join(parts)

