import json
import numpy as np
import plotly.graph_objects as go
import polars as pl

def _fig(f):
    return json.loads(f.to_json())

def run(df, df_full, semantic_types, groups, context: dict | None = None):
    dt_cols = groups.get("datetime", [])
    num_cols = groups.get("numeric_continuous", []) + groups.get("numeric_discrete", [])

    if not dt_cols or not num_cols:
        return {"active": False, "reason": "Nessuna colonna datetime o numerica rilevata"}

    ts_col = dt_cols[0]
    # Priorità: se sono presenti feature derivate da date (es. *_year, *_month),
    # includile subito come "value columns" per renderle visibili in TimeSeries.
    derived_time_cols = [c for c in num_cols if c.endswith("_year") or c.endswith("_month")]
    val_cols = (derived_time_cols + [c for c in num_cols if c not in derived_time_cols])[:3]
    results = {"active": True, "ts_column": ts_col, "analyses": {}}

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
    vals = ts[val_col].cast(pl.Float64).to_numpy()
    min_dt = str(ts[ts_col].min())
    max_dt = str(ts[ts_col].max())

    # Line chart
    fig_line = go.Figure()
    fig_line.add_trace(
        go.Scatter(
            x=[str(d) for d in dates],
            y=vals.tolist(),
            mode="lines",
            line=dict(color="#2B2B2B", width=1.5),
            name=val_col,
        )
    )
    # Rolling mean 10%
    w = max(3, n // 10)
    rolling = np.convolve(vals, np.ones(w) / w, mode="valid")
    fig_line.add_trace(
        go.Scatter(
            x=[str(d) for d in dates[w - 1 :]],
            y=rolling.tolist(),
            mode="lines",
            line=dict(color="#FF4D00", width=2, dash="dash"),
            name=f"Media mobile ({w})",
        )
    )
    
    # Change points
    change_points = _cusum_change_points(vals)
    for cp in change_points:
        cp_idx = min(cp, len(dates)-1)
        fig_line.add_vline(x=str(dates[cp_idx]), line=dict(color="red", dash="dot"), annotation_text="Change Point")

    fig_line.update_layout(
        title=f"Serie temporale — {val_col}",
        xaxis_title="Data",
        yaxis_title=val_col,
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#FFFFFF",
        font=dict(family="JetBrains Mono", size=11),
        margin=dict(t=50, b=60, l=60, r=20),
    )

    # Stazionarietà (ADF & KPSS)
    adf_res = _adf_test(vals)
    kpss_res = _kpss_test(vals)
    
    stationarity = {
        "adf": adf_res,
        "kpss": kpss_res,
        "is_stationary": (adf_res.get("decision") == "stazionaria" and kpss_res.get("decision") == "stazionaria")
    }

    # ACF/PACF
    acf_vals, pacf_vals, fig_acf, fig_pacf = _acf_pacf(vals, min(40, n // 3), val_col)
    
    # STL Decomposition
    stl_res = _stl_decomposition(vals, dates, val_col)

    comment = _ts_comment(stationarity, acf_vals, change_points, val_col)

    return {
        "metadata": {
            "n_observations": n,
            "min_date": min_dt,
            "max_date": max_dt,
        },
        "stationarity": stationarity,
        "change_points_indices": change_points,
        "acf": acf_vals,
        "pacf": pacf_vals,
        "charts": {
            "line": _fig(fig_line), 
            "acf": _fig(fig_acf) if fig_acf else None,
            "pacf": _fig(fig_pacf) if fig_pacf else None,
            "stl": _fig(stl_res) if stl_res else None
        },
        "ai_comment": comment,
    }

def _adf_test(arr):
    try:
        from statsmodels.tsa.stattools import adfuller
        r = adfuller(arr, autolag="AIC")
        return {
            "test": "ADF",
            "statistic": round(float(r[0]), 4),
            "pvalue": round(float(r[1]), 4),
            "decision": "stazionaria" if r[1] < 0.05 else "non stazionaria",
        }
    except Exception as e:
        return {"test": "ADF", "error": str(e)}

def _kpss_test(arr):
    try:
        from statsmodels.tsa.stattools import kpss
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = kpss(arr, regression='c', nlags="auto")
        return {
            "test": "KPSS",
            "statistic": round(float(r[0]), 4),
            "pvalue": round(float(r[1]), 4),
            "decision": "non stazionaria" if r[1] < 0.05 else "stazionaria", # p<0.05 means reject null of stationarity
        }
    except Exception as e:
        return {"test": "KPSS", "error": str(e)}

def _acf_pacf(arr, max_lag=40, val_col=""):
    try:
        from statsmodels.tsa.stattools import acf, pacf
        acf_vals = acf(arr, nlags=max_lag).tolist()
        pacf_vals = pacf(arr, nlags=max_lag, method='ywm').tolist()
        
        n = len(arr)
        conf = 1.96 / np.sqrt(n)
        
        fig_acf = go.Figure()
        fig_acf.add_trace(go.Bar(x=list(range(len(acf_vals))), y=acf_vals, marker_color="#2B2B2B", name="ACF"))
        fig_acf.add_hline(y=conf, line=dict(color="#FF4D00", dash="dash"))
        fig_acf.add_hline(y=-conf, line=dict(color="#FF4D00", dash="dash"))
        fig_acf.update_layout(title=f"ACF — {val_col}", plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF")
        
        fig_pacf = go.Figure()
        fig_pacf.add_trace(go.Bar(x=list(range(len(pacf_vals))), y=pacf_vals, marker_color="#2B2B2B", name="PACF"))
        fig_pacf.add_hline(y=conf, line=dict(color="#FF4D00", dash="dash"))
        fig_pacf.add_hline(y=-conf, line=dict(color="#FF4D00", dash="dash"))
        fig_pacf.update_layout(title=f"PACF — {val_col}", plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF")
        
        return [round(x, 4) for x in acf_vals], [round(x, 4) for x in pacf_vals], fig_acf, fig_pacf
    except Exception:
        return [], [], None, None

def _stl_decomposition(arr, dates, val_col):
    try:
        from statsmodels.tsa.seasonal import STL
        import pandas as pd
        # Assumiamo un periodo standard se non noto, es 7 per dati giornalieri, o usiamo un euristica
        # statsmodels richiede un periodo se pandas series non ha frequenza
        res = STL(arr, period=min(13, max(2, len(arr)//10))).fit()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[str(d) for d in dates], y=res.trend.tolist(), name="Trend"))
        fig.add_trace(go.Scatter(x=[str(d) for d in dates], y=res.seasonal.tolist(), name="Seasonal"))
        fig.add_trace(go.Scatter(x=[str(d) for d in dates], y=res.resid.tolist(), name="Residual", mode="markers"))
        fig.update_layout(title=f"STL Decomposition — {val_col}", plot_bgcolor="#F5F5F5", paper_bgcolor="#FFFFFF")
        return fig
    except Exception:
        return None

def _cusum_change_points(arr, threshold=5.0):
    # Semplice CUSUM basato sulla media
    mean = np.mean(arr)
    std = np.std(arr)
    if std == 0: return []
    
    s_hi = 0
    s_lo = 0
    change_points = []
    
    for i, x in enumerate(arr):
        z = (x - mean) / std
        s_hi = max(0, s_hi + z - 0.5)
        s_lo = max(0, s_lo - z - 0.5)
        
        if s_hi > threshold or s_lo > threshold:
            change_points.append(i)
            s_hi = 0
            s_lo = 0
            mean = np.mean(arr[i:])
            std = np.std(arr[i:])
            if std == 0: break
            
    return change_points

def _ts_comment(stationarity, acf_vals, change_points, col):
    comments = []
    adf = stationarity.get("adf", {})
    kpss = stationarity.get("kpss", {})
    
    if adf.get("decision") and kpss.get("decision"):
        is_stat = stationarity.get("is_stationary")
        comments.append({
            "role": "data_scientist",
            "insight": f"La serie '{col}' risulta {'stazionaria' if is_stat else 'non stazionaria'} (ADF: {adf['decision']}, KPSS: {kpss['decision']})."
        })
        if not is_stat:
            comments.append({
                "role": "ml_engineer",
                "insight": "Essendo non stazionaria, valutare differenziazione o log-transform per modelli ARIMA/VAR."
            })
            
    significant_lags = [i for i, v in enumerate(acf_vals[1:], 1) if abs(v) > 0.2]
    if significant_lags:
        comments.append({
            "role": "ts_analyst",
            "insight": f"Rilevata autocorrelazione significativa ai lag: {significant_lags[:5]}. Utile per determinare l'ordine AR/MA."
        })
        
    if change_points:
        comments.append({
            "role": "ts_analyst",
            "insight": f"Rilevati {len(change_points)} change point(s) strutturali (CUSUM). Attenzione a shift di regime nei dati."
        })
        
    return comments
