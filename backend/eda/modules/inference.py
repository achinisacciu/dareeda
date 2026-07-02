import numpy as np
import polars as pl
from scipy import stats as sp


def run(df, df_full, semantic_types, groups):
    num_cols = groups.get("numeric_continuous", []) + groups.get("numeric_discrete", [])
    cat_cols = groups.get("categorical_nominal", []) + groups.get("categorical_ordinal", [])
    bool_cols = groups.get("boolean", [])

    results = []
    target_bins = bool_cols[:2] + [c for c in cat_cols if df[c].drop_nulls().n_unique() <= 5][:2]

    for num in num_cols[:8]:
        for bin_col in target_bins[:3]:
            r = _run_test(df, num, bin_col)
            if r:
                results.append(r)

    # FDR correction
    results = _fdr_correction(results)

    summary = {
        "n_tests": len(results),
        "significant_after_fdr": sum(1 for r in results if r.get("significant_fdr", False)),
    }

    return {
        "tests": results[:40],
        "summary": summary,
        "ai_comment": _comment(summary, results),
    }


def _run_test(df, num_col, group_col):
    try:
        groups_list = df[group_col].drop_nulls().cast(pl.String).unique().sort().to_list()
        if len(groups_list) < 2 or len(groups_list) > 10:
            return None

        arrays = []
        for g in groups_list:
            mask = df[group_col].cast(pl.String) == g
            vals = df[num_col].filter(mask).drop_nulls().cast(pl.Float64).to_numpy()
            if len(vals) >= 5:
                arrays.append((g, vals))

        if len(arrays) < 2:
            return None

        if len(arrays) == 2:
            # t-test + Mann-Whitney
            a1, a2 = arrays[0][1], arrays[1][1]
            t_stat, t_p = sp.ttest_ind(a1, a2, equal_var=False)
            u_stat, u_p = sp.mannwhitneyu(a1, a2, alternative="two-sided")
            # Cohen's d
            pooled_std = np.sqrt((a1.std() ** 2 + a2.std() ** 2) / 2)
            cohens_d = float((a1.mean() - a2.mean()) / pooled_std) if pooled_std > 0 else 0.0
            return {
                "feature": num_col,
                "target": group_col,
                "test": "t-test + Mann-Whitney",
                "pvalue": round(float(u_p), 4),
                "effect_size": round(cohens_d, 4),
                "effect_label": _cohens_d_label(abs(cohens_d)),
                "significant": u_p < 0.05,
                "groups": [g for g, _ in arrays],
                "group_means": {g: round(float(arr.mean()), 4) for g, arr in arrays},
            }
        else:
            # ANOVA + Kruskal-Wallis
            f_stat, f_p = sp.f_oneway(*[arr for _, arr in arrays])
            h_stat, h_p = sp.kruskal(*[arr for _, arr in arrays])
            return {
                "feature": num_col,
                "target": group_col,
                "test": "ANOVA + Kruskal-Wallis",
                "pvalue": round(float(h_p), 4),
                "effect_size": None,
                "effect_label": None,
                "significant": h_p < 0.05,
                "groups": [g for g, _ in arrays],
                "group_means": {g: round(float(arr.mean()), 4) for g, arr in arrays},
            }
    except Exception:
        return None


def _cohens_d_label(d):
    if d < 0.2:
        return "trascurabile"
    elif d < 0.5:
        return "piccolo"
    elif d < 0.8:
        return "medio"
    return "grande"


def _fdr_correction(results):
    """Benjamini-Hochberg step-up procedure. Trova il max k con p(k) <= k/n * alpha."""
    if not results:
        return results
    pvals = np.array([r["pvalue"] for r in results])
    n = len(pvals)
    order = np.argsort(pvals)
    sorted_p = pvals[order]
    # ponytail: BH step-up — trova il massimo rango k che soddisfa la soglia
    thresholds = np.arange(1, n + 1) / n * 0.05
    below = sorted_p <= thresholds
    max_k = np.where(below)[0][-1] + 1 if below.any() else 0
    # Tutti i p-value con rango <= max_k sono significativi
    significant_fdr = np.zeros(n, dtype=bool)
    for rank, idx in enumerate(order):
        if rank < max_k:
            significant_fdr[idx] = True
    for i, r in enumerate(results):
        r["significant_fdr"] = bool(significant_fdr[i])
    return results


def _comment(summary, results):
    n = summary["n_tests"]
    n_sig = summary["significant_after_fdr"]
    parts = [f"Eseguiti {n} test statistici."]
    if n_sig == 0:
        parts.append(
            "Nessuna associazione significativa rilevata dopo correzione FDR (Benjamini-Hochberg)."
        )
    else:
        parts.append(
            f"Dopo correzione FDR, {n_sig} associazioni risultano statisticamente significative."
        )
        top = [r for r in results if r.get("significant_fdr")]
        if top:
            t = top[0]
            eff = f", effect size {t.get('effect_label', '')}" if t.get("effect_label") else ""
            parts.append(
                f"Associazione più forte: {t['feature']} × {t['target']} (p={t['pvalue']}{eff})."
            )
    return " ".join(parts)
