import polars as pl

from core.semantic_typer import type_dataframe, group_by_semantic
from eda.modules import data_quality


def test_missing_heatmap_uses_full_dataset_rows():
    n_rows = 650
    df = pl.DataFrame({
        "a": [None if idx >= 640 else idx for idx in range(n_rows)],
        "b": [idx for idx in range(n_rows)],
    })

    semantic_types = type_dataframe(df)
    groups = group_by_semantic(semantic_types)
    result = data_quality.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)

    heatmap = result["missing"]["charts"]["missing_heatmap"]

    assert heatmap is not None
    assert len(heatmap["data"][0]["z"]) == n_rows
    assert "campione" not in heatmap["layout"]["title"]["text"].lower()


def test_missing_cooccurrence_is_not_truncated_to_first_20k_rows():
    n_rows = 20_050
    df = pl.DataFrame({
        "col_a": [idx if idx < (n_rows - 5) else None for idx in range(n_rows)],
        "col_b": [idx * 2 if idx < (n_rows - 5) else None for idx in range(n_rows)],
    })

    semantic_types = type_dataframe(df)
    groups = group_by_semantic(semantic_types)
    result = data_quality.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)

    cooccurrence = result["missing"]["charts"]["missing_cooccurrence"]
    assert cooccurrence is not None
    assert cooccurrence["data"][0]["z"][0][1] == 5
    assert cooccurrence["data"][0]["z"][1][0] == 5
