import polars as pl

from core.semantic_typer import type_dataframe, group_by_semantic
from eda.modules import data_quality


def test_data_quality_builds_explicit_cleaning_proposals():
    df = pl.DataFrame({
        "status": ["ok", " N/A ", "ok", "null", " active ", "ok"],
        "notes": ["  alpha", "beta  ", "gamma", "delta", "epsilon", "zeta"],
        "constant_flag": ["Y", "Y", "Y", "Y", "Y", "Y"],
        "value": [1, 1, 2, 2, 3, 3],
    })

    df = pl.concat([df, df.slice(0, 1)], how="vertical")

    semantic_types = type_dataframe(df)
    groups = group_by_semantic(semantic_types)

    result = data_quality.run(df=df, df_full=df, semantic_types=semantic_types, groups=groups)

    issues = result["standardized_issues"]
    issue_types = {issue["action"]["type"] for issue in issues}

    assert "drop_duplicate_rows" in issue_types
    assert "replace_values" in issue_types
    assert "trim_whitespace" in issue_types
    assert "exclude_column" in issue_types

    replace_issue = next(issue for issue in issues if issue["action"]["type"] == "replace_values")
    assert replace_issue["proposal"]["supported"] is True
    assert replace_issue["proposal"]["method"]["uses_regex"] is False
    assert replace_issue["action"]["params"]["match_mode"] == "exact_case_insensitive_trimmed"

    trim_issue = next(issue for issue in issues if issue["action"]["type"] == "trim_whitespace")
    assert trim_issue["proposal"]["result"]
    assert trim_issue["preview"]["examples"]

    exclude_issue = next(issue for issue in issues if issue["action"]["type"] == "exclude_column")
    assert "Colonne stimate" in exclude_issue["proposal"]["result"]
