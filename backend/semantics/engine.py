from .feature_engineering.registry import FEATURE_RULES
from .registry import DETECTORS


def analyze_dataset(df):
    results = {}

    for col in df.columns:
        col_results = []

        for detector in DETECTORS:
            try:
                res = detector.detect(df, col)
                if res and res.get("confidence", 0) > 0.5:
                    col_results.append(res)
            except Exception:
                pass

        # scegli il migliore
        best = max(col_results, key=lambda x: x["confidence"], default=None)

        results[col] = {
            "semantic_type": best["semantic_type"] if best else "unknown",
            "confidence": best["confidence"] if best else 0.0,
            "candidates": col_results,
        }

    # Feature Engineering
    suggested_features = []
    for rule in FEATURE_RULES:
        try:
            features = rule.apply(df, results)
            if features:
                suggested_features.extend(features)
        except Exception:
            pass

    return {"columns": results, "suggested_features": suggested_features}
