import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import polars as pl
from core.semantic_typer import type_dataframe, group_by_semantic
from eda.modules import overview, data_quality, univariate
import random

# Dataset di test
random.seed(42)
df = pl.DataFrame({
    "id":       [str(i) for i in range(200)],
    "price":    [random.uniform(10, 500) for _ in range(200)],
    "rating":   [random.choice([1,2,3,4,5]) for _ in range(200)],
    "category": [random.choice(["A","B","C","D"]) for _ in range(200)],
    "active":   [random.choice([True, False]) for _ in range(200)],
    "notes":    [f"Note di testo numero {i} con descrizione lunga abbastanza" for i in range(200)],
})
# Aggiungi alcuni missing
import numpy as np
mask = pl.Series([None if random.random() < 0.1 else v for v in df["price"].to_list()])
df = df.with_columns(mask.alias("price"))

semantic_types = type_dataframe(df)
groups = group_by_semantic(semantic_types)

print("Tipi rilevati:")
for col, t in semantic_types.items():
    print(f"  {col}: {t}")

r_overview = overview.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)
assert "n_rows" in r_overview
assert r_overview["n_rows"] == 200
print(f"\noverview OK — {r_overview['n_rows']} righe, {r_overview['n_cols']} colonne, {r_overview['pct_missing_global']}% missing")

r_dq = data_quality.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)
assert "missing" in r_dq
assert "duplicates" in r_dq
print(f"data_quality OK — {r_dq['duplicates']['n_duplicate_rows']} duplicati")

r_uni = univariate.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)
assert "price" in r_uni
assert "charts" in r_uni["price"]
print(f"univariate OK — {len(r_uni)} colonne analizzate")

print("\nFase 2: tutti i moduli operativi.")
