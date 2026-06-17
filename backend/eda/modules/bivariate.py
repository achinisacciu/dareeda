"""Bivariate analysis module — numeric×numeric, numeric×categorical, categorical×categorical."""

from __future__ import annotations

import json
import logging
from typing import Any

import numpy as np
import plotly.graph_objects as go
import polars as pl
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)

__all__ = ["run"]

# ── Constants ──────────────────────────────────────────────────────────────────

_MAX_NUMERIC_COLS = 20  # max numeric columns to consider
_MAX_NUM_NUM_PAIRS = 30  # max pairs returned in num×num
_MAX_SCATTER_POINTS = 2000  # downsample for scatter plots
_MAX_TOP_SCATTERS = 5  # top-N scatter plots by |r|

_MAX_NUM_CAT_NUM = 5  # max numeric cols in num×cat
_MAX_NUM_CAT_CAT = 3  # max categorical cols in num×cat
_MAX_NUM_CAT_PAIRS = 9  # max pairs analysed in num×cat
_MAX_BOX_GROUPS = 8  # max category values per box-plot

_MAX_CAT_CAT_COLS = 6  # max categorical columns in cat×cat
_MAX_CAT_CAT_PAIRS = 6  # max pairs analysed in cat×cat

_CORR_HIGH = 0.7  # threshold for "high correlation"
_CORR_MULTICOL = 0.85  # threshold for multicollinearity warning
_CRAMERS_STRONG = 0.3  # threshold for "strong association"

_MIN_OBS_CORR = 10  # min observations for correlation
_MIN_OBS_GROUP = 3  # min observations per group in box-plot

# Plotly theme defaults
_PLOT_THEME = {
    "plot_bgcolor": "#F5F5F5",
    "paper_bgcolor": "#FFFFFF",
    "font": dict(family="JetBrains Mono", size=11),
}
_HEATMAP_THEME = {
    "plot_bgcolor": "#FFFFFF",
    "paper_bgcolor": "#FFFFFF",
    "font": dict(family="JetBrains Mono", size=10),
}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _fig_to_json(fig: go.Figure) -> dict[str, Any]:
    """Serialise a Plotly Figure to a JSON-compatible dict."""
    return json.loads(fig.to_json())


def _safe_pearsonr(
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[float, float]:
    """Compute Pearson r with a guard for constant arrays."""
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0, 1.0
    r, p = scipy_stats.pearsonr(x, y)
    return float(r), float(p)


def _safe_spearmanr(
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[float, float]:
    """Compute Spearman rho with a guard for constant arrays."""
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0, 1.0
    r, p = scipy_stats.spearmanr(x, y)
    return float(r), float(p)


def _cramers_v(ct: np.ndarray) -> float:
    """Compute bias-corrected Cramér's V from a contingency table.

    Uses the Bergsma & Wagenmakers correction for small samples.
    Falls back to the standard formula when the correction would be invalid.
    """
    n = ct.sum()
    if n == 0:
        return 0.0
    chi2 = scipy_stats.chi2_contingency(ct)[0]
    k = min(ct.shape)
    if k < 2:
        return 0.0
    # Bias-corrected Cramér's V
    phi2 = chi2 / n
    phi2_corr = max(0.0, phi2 - ((k - 1) / (n - 1))) if n > k else phi2
    k_corr = k - ((k - 1) ** 2) / (n - 1) if n > k else k
    if k_corr <= 0:
        return 0.0
    v = np.sqrt(phi2_corr / (k_corr - 1))
    return float(min(v, 1.0))  # cap at 1.0 for numerical stability


# ── Public entry point ─────────────────────────────────────────────────────────


def run(
    df: pl.DataFrame,
    df_full: pl.DataFrame,
    semantic_types: dict[str, str],
    groups: dict[str, list[str]],
) -> dict[str, Any]:
    """Run bivariate analysis across all three axis types.

    Parameters
    ----------
    df : pl.DataFrame
        Working dataframe (possibly sampled).
    df_full : pl.DataFrame
        Full dataframe (unused here, kept for API consistency).
    semantic_types : dict
        Column → semantic type mapping (unused here).
    groups : dict
        Column group mapping (e.g. ``{"numeric_continuous": [...]}``).

    Returns
    -------
    dict with keys ``"num_num"``, ``"num_cat"``, ``"cat_cat"``.
    """
    num_cols = groups.get("numeric_continuous", []) + groups.get("numeric_discrete", [])
    cat_cols = groups.get("categorical_nominal", []) + groups.get("categorical_ordinal", [])

    return {
        "num_num": _num_num(df, num_cols),
        "num_cat": _num_cat(df, num_cols, cat_cols),
        "cat_cat": _cat_cat(df, cat_cols),
    }


# ── Numeric × Numeric ─────────────────────────────────────────────────────────


def _num_num(df: pl.DataFrame, num_cols: list[str]) -> dict[str, Any]:
    """Correlation analysis (Pearson + Spearman) and scatter plots."""
    if len(num_cols) < 2:
        return {"skipped": True, "reason": "Meno di 2 colonne numeriche"}

    cols = num_cols[:_MAX_NUMERIC_COLS]
    pairs: list[dict[str, Any]] = []

    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            va = df[a].drop_nulls().cast(pl.Float64)
            vb = df[b].drop_nulls().cast(pl.Float64)
            n_min = min(len(va), len(vb))
            if n_min < _MIN_OBS_CORR:
                continue
            arr_a = va[:n_min].to_numpy()
            arr_b = vb[:n_min].to_numpy()

            pr, _ = _safe_pearsonr(arr_a, arr_b)
            sr, _ = _safe_spearmanr(arr_a, arr_b)

            pairs.append({
                "var_a": a,
                "var_b": b,
                "pearson_r": round(pr, 4),
                "spearman_rho": round(sr, 4),
                "n": n_min,
                "note": "Alta correlazione" if abs(pr) > _CORR_HIGH else "",
            })

    pairs.sort(key=lambda p: abs(p["pearson_r"]), reverse=True)

    # ── Correlation heatmap ────────────────────────────────────────────────
    heatmap_fig = _build_correlation_heatmap(cols, pairs)

    # ── Top-N scatter plots ────────────────────────────────────────────────
    scatters = _build_top_scatters(df, pairs[:_MAX_TOP_SCATTERS])

    comment = _comment_num_num(pairs)

    return {
        "pairs": pairs[:_MAX_NUM_NUM_PAIRS],
        "charts": {"correlation_heatmap": _fig_to_json(heatmap_fig), "scatters": scatters},
        "ai_comment": comment,
    }


def _build_correlation_heatmap(
    cols: list[str],
    pairs: list[dict[str, Any]],
) -> go.Figure:
    """Build the Pearson correlation heatmap."""
    n = len(cols)
    arr = np.zeros((n, n))
    idx = {c: i for i, c in enumerate(cols)}

    for p in pairs:
        i, j = idx[p["var_a"]], idx[p["var_b"]]
        arr[i][j] = arr[j][i] = p["pearson_r"]
    np.fill_diagonal(arr, 1.0)

    fig = go.Figure(
        go.Heatmap(
            z=arr.tolist(),
            x=cols,
            y=cols,
            colorscale=[[0, "#2B2B2B"], [0.5, "#FFFFFF"], [1, "#FF4D00"]],
            zmid=0,
            zmin=-1,
            zmax=1,
            text=[[f"{arr[i][j]:.2f}" for j in range(n)] for i in range(n)],
            texttemplate="%{text}",
            showscale=True,
        )
    )
    fig.update_layout(
        title="Matrice di correlazione (Pearson)",
        margin=dict(t=50, b=100, l=100, r=20),
        xaxis=dict(tickangle=-45),
        **_HEATMAP_THEME,
    )
    return fig


def _build_top_scatters(
    df: pl.DataFrame,
    top_pairs: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build scatter + trend-line plots for the top correlated pairs."""
    scatters: dict[str, dict[str, Any]] = {}

    for p in top_pairs:
        a, b = p["var_a"], p["var_b"]
        try:
            arr_a = df[a].drop_nulls().cast(pl.Float64).to_numpy()
            arr_b = df[b].drop_nulls().cast(pl.Float64).to_numpy()
            n = min(len(arr_a), len(arr_b), _MAX_SCATTER_POINTS)

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=arr_a[:n].tolist(),
                    y=arr_b[:n].tolist(),
                    mode="markers",
                    marker=dict(color="#2B2B2B", size=4, opacity=0.6),
                )
            )

            # Trend line (robust against NaN / constant arrays)
            x_seg, y_seg = arr_a[:n], arr_b[:n]
            valid = ~(np.isnan(x_seg) | np.isnan(y_seg) | np.isinf(x_seg) | np.isinf(y_seg))
            x_clean, y_clean = x_seg[valid], y_seg[valid]
            if len(x_clean) >= 2 and np.std(x_clean) > 0:
                m, q = np.polyfit(x_clean, y_clean, 1)
                xr = [float(x_clean.min()), float(x_clean.max())]
                fig.add_trace(
                    go.Scatter(
                        x=xr,
                        y=[m * x + q for x in xr],
                        mode="lines",
                        line=dict(color="#FF4D00", width=2),
                        name="Trend",
                    )
                )

            fig.update_layout(
                title=f"Scatter: {a} × {b}  (r={p['pearson_r']})",
                xaxis_title=a,
                yaxis_title=b,
                margin=dict(t=50, b=50, l=60, r=20),
                showlegend=False,
                **_PLOT_THEME,
            )
            scatters[f"{a}_x_{b}"] = _fig_to_json(fig)
        except Exception:
            logger.warning("Failed to build scatter for %s × %s", a, b, exc_info=True)

    return scatters


def _comment_num_num(pairs: list[dict[str, Any]]) -> str:
    """Generate a short natural-language summary of num×num results."""
    if not pairs:
        return "Analisi bivariata numerica non disponibile (meno di 2 colonne)."

    high = [p for p in pairs if abs(p["pearson_r"]) > _CORR_HIGH]
    multi = [p for p in pairs if abs(p["pearson_r"]) > _CORR_MULTICOL]
    parts: list[str] = []

    if high:
        top = high[0]
        parts.append(
            f"La coppia con correlazione più elevata è {top['var_a']} × {top['var_b']} (r={top['pearson_r']})."
        )
    if multi:
        parts.append(
            f"Rilevata potenziale multicollinearità in {len(multi)} coppie (|r|>{_CORR_MULTICOL}). "
            "Valutare rimozione di feature ridondanti."
        )
    if not high:
        parts.append("Nessuna correlazione lineare forte rilevata tra le variabili numeriche.")

    return " ".join(parts)


# ── Numeric × Categorical ─────────────────────────────────────────────────────


def _num_cat(
    df: pl.DataFrame,
    num_cols: list[str],
    cat_cols: list[str],
) -> dict[str, Any]:
    """Box-plot and per-group statistics for numeric columns across categories."""
    if not num_cols or not cat_cols:
        return {"skipped": True, "reason": "Colonne numeriche o categoriche insufficienti"}

    results: list[dict[str, Any]] = []
    charts: dict[str, dict[str, Any]] = {}
    pairs_done = 0

    for num in num_cols[:_MAX_NUM_CAT_NUM]:
        if pairs_done >= _MAX_NUM_CAT_PAIRS:
            break
        for cat in cat_cols[:_MAX_NUM_CAT_CAT]:
            if pairs_done >= _MAX_NUM_CAT_PAIRS:
                break
            try:
                result, chart_key, chart_json = _num_cat_one_pair(df, num, cat)
                if result is None:
                    continue
                results.append(result)
                charts[chart_key] = chart_json
                pairs_done += 1
            except Exception:
                logger.warning("num×cat failed for %s × %s", num, cat, exc_info=True)

    return {"pairs": results, "charts": charts}


def _num_cat_one_pair(
    df: pl.DataFrame,
    num: str,
    cat: str,
) -> tuple[dict[str, Any] | None, str, dict[str, Any]]:
    """Analyse a single numeric × categorical pair.

    Returns ``(result_dict, chart_key, chart_json)`` or ``(None, "", {})``
    if the pair cannot be analysed.
    """
    cat_vals = df[cat].drop_nulls().cast(pl.String)
    groups_list = cat_vals.unique().sort().to_list()[:_MAX_BOX_GROUPS]
    if len(groups_list) < 2:
        return None, "", {}

    group_stats: list[dict[str, Any]] = []
    group_arrays: list[tuple[str, np.ndarray]] = []

    for g in groups_list:
        mask = df[cat].cast(pl.String) == g
        vals = df[num].filter(mask).drop_nulls().cast(pl.Float64).to_numpy()
        if len(vals) < _MIN_OBS_GROUP:
            continue
        group_stats.append({
            "group": g,
            "count": len(vals),
            "mean": round(float(vals.mean()), 3),
            "median": round(float(np.median(vals)), 3),
            "std": round(float(vals.std()), 3),
        })
        group_arrays.append((g, vals))

    if len(group_arrays) < 2:
        return None, "", {}

    # Box plot
    fig = go.Figure()
    for g, arr in group_arrays:
        fig.add_trace(
            go.Box(
                y=arr.tolist(),
                name=str(g),
                marker_color="#FF4D00",
                line_color="#000000",
                boxmean=False,
            )
        )
    fig.update_layout(
        title=f"{num} per {cat}",
        yaxis_title=num,
        margin=dict(t=50, b=60, l=60, r=20),
        **_PLOT_THEME,
    )

    chart_key = f"{num}_by_{cat}"
    result = {"num": num, "cat": cat, "group_stats": group_stats}
    return result, chart_key, _fig_to_json(fig)


# ── Categorical × Categorical ─────────────────────────────────────────────────


def _cat_cat(df: pl.DataFrame, cat_cols: list[str]) -> dict[str, Any]:
    """Chi-squared test and Cramér's V for categorical pairs."""
    if len(cat_cols) < 2:
        return {"skipped": True, "reason": "Meno di 2 colonne categoriche"}

    results: list[dict[str, Any]] = []
    pairs_done = 0

    for i, a in enumerate(cat_cols[:_MAX_CAT_CAT_COLS]):
        if pairs_done >= _MAX_CAT_CAT_PAIRS:
            break
        for b in cat_cols[i + 1 : _MAX_CAT_CAT_COLS]:
            if pairs_done >= _MAX_CAT_CAT_PAIRS:
                break
            try:
                result = _cat_cat_one_pair(df, a, b)
                if result is not None:
                    results.append(result)
                    pairs_done += 1
            except Exception:
                logger.warning("cat×cat failed for %s × %s", a, b, exc_info=True)

    results.sort(key=lambda x: x["cramers_v"], reverse=True)
    return {"pairs": results}


def _cat_cat_one_pair(
    df: pl.DataFrame,
    a: str,
    b: str,
) -> dict[str, Any] | None:
    """Analyse a single categorical × categorical pair.

    Returns a result dict or ``None`` if the pair cannot be analysed.
    """
    va = df[a].drop_nulls().cast(pl.String)
    vb = df[b].drop_nulls().cast(pl.String)
    n = min(len(va), len(vb))

    arr_a = va[:n].to_numpy().astype(str)
    arr_b = vb[:n].to_numpy().astype(str)

    # Build contingency table using numpy (no sklearn dependency)
    labels_a, inv_a = np.unique(arr_a, return_inverse=True)
    labels_b, inv_b = np.unique(arr_b, return_inverse=True)
    ct = np.zeros((len(labels_a), len(labels_b)), dtype=int)
    for x, y in zip(inv_a, inv_b, strict=False):
        ct[x][y] += 1

    chi2, p, dof, _ = scipy_stats.chi2_contingency(ct)
    cramers_v = _cramers_v(ct)

    return {
        "var_a": a,
        "var_b": b,
        "cramers_v": round(cramers_v, 4),
        "chi2_pvalue": round(float(p), 4),
        "note": "Associazione forte" if cramers_v > _CRAMERS_STRONG else "",
    }
