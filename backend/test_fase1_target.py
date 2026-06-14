import sys
from pathlib import Path

# Add backend dir to path for imports
sys.path.append(str(Path(__file__).parent.absolute()))

import polars as pl
from eda.modules import ml_exploratory


def test_ml_exploratory():
    print("\n" + "="*50)
    print("=== TEST FASE 1: TARGET SELECTION ===")
    print("="*50)

    df = pl.DataFrame({
        "num1": [1.0, 2.0, 3.0, 4.0, 5.0]*4,
        "num2": [5.0, 4.0, 3.0, 2.0, 1.0]*4,
        "num3": [1.2, 3.4, 5.6, 7.8, 9.0]*4,
        "target_valid": [1.0, 0.0, 1.0, 0.0, 1.0]*4,
        "target_null": [None, None, None, None, None]*4,
        "cat1": ["A", "B", "A", "B", "A"]*4
    })

    df_full = df
    semantic_types = {
        "num1": "numeric_continuous",
        "num2": "numeric_continuous",
        "num3": "numeric_continuous",
        "target_valid": "numeric_discrete",
        "target_null": "numeric_continuous",
        "cat1": "categorical_nominal"
    }
    groups = {
        "numeric_continuous": ["num1", "num2", "num3", "target_null"],
        "numeric_discrete": ["target_valid"],
        "categorical_nominal": ["cat1"],
        "boolean": []
    }

    print("\n[Caso 2] Target mancante:")
    res2 = ml_exploratory.run(df, df_full, semantic_types, groups, context={})
    print(res2)
    assert "error" in res2

    print("\n[Caso 3] Target non esiste:")
    res3 = ml_exploratory.run(df, df_full, semantic_types, groups, context={"target": "inesistente", "problem_type": "regression"})
    print(res3)
    assert "error" in res3

    print("\n[Caso 4] Target tutta null:")
    res4 = ml_exploratory.run(df, df_full, semantic_types, groups, context={"target": "target_null", "problem_type": "regression"})
    print(res4)
    assert "error" in res4

    print("\n[Caso 1] Target valida:")
    # Target valid requires classification or regression
    res1 = ml_exploratory.run(df, df_full, semantic_types, groups, context={"target": "target_valid", "problem_type": "classification"})
    print({k: v.get("skipped", False) for k, v in res1.items() if isinstance(v, dict)})
    print("Test passed successfully!")

if __name__ == "__main__":
    test_ml_exploratory()
