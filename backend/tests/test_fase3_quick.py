import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import polars as pl

random.seed(42)
np.random.seed(42)

from core.semantic_typer import group_by_semantic, type_dataframe
from eda.modules import bivariate, inference, ml_exploratory, multivariate, timeseries

df = pl.DataFrame({
    "id":     [str(i) for i in range(300)],
    "price":  [random.gauss(100, 30) for _ in range(300)],
    "qty":    [random.randint(1, 50) for _ in range(300)],
    "cost":   [random.gauss(60, 20) for _ in range(300)],
    "score":  [random.gauss(5, 1) for _ in range(300)],
    "cat":    [random.choice(["A","B","C"]) for _ in range(300)],
    "active": [random.choice([True, False]) for _ in range(300)],
})

semantic_types = type_dataframe(df)
groups = group_by_semantic(semantic_types)

r_biv = bivariate.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)
assert "num_num" in r_biv and "pairs" in r_biv["num_num"]
print(f"bivariate OK — {len(r_biv['num_num']['pairs'])} coppie num×num")

r_mul = multivariate.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)
assert "pca" in r_mul
print(f"multivariate OK — PCA: {r_mul['pca'].get('n_components_used', 'skipped')}")

r_ts = timeseries.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)
print(f"timeseries OK — active: {r_ts.get('active', False)}")

r_ml = ml_exploratory.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)
assert "clustering" in r_ml
k = r_ml["clustering"].get("best_k", "skipped")
print(f"ml_exploratory OK — best K={k}")

r_inf = inference.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)
n_tests = r_inf["summary"]["n_tests"]
print(f"inference OK — {n_tests} test eseguiti")

print("\nFase 3: tutti i moduli EDA operativi.")
