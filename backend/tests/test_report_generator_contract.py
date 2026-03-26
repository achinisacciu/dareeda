from pathlib import Path

from core.report_generator import _generate_typst


def test_report_generator_includes_professional_sections_and_decisions():
    cleaning_actions = [
        {"type": "drop_duplicate_rows"},
        {"type": "trim_whitespace", "column": "city", "params": {}},
    ]

    analysis_data = {
        "analysis_id": "analysis-001",
        "dataset_filename": "sales.csv",
        "tool_version": "1.0.0",
        "sampled": True,
        "sample_n": 50000,
        "n_rows_full": 120000,
        "n_cols": 6,
        "target": "revenue",
        "problem_type": "regression",
        "derived_columns": ["margin_pct"],
        "accepted_features": [{"name": "margin_pct"}],
        "analysis_context": {
            "target": "revenue",
            "problem_type": "regression",
            "accepted_feature_names": ["margin_pct"],
            "cleaning_actions": cleaning_actions,
            "sampling": {
                "sampled": True,
                "sample_n": 50000,
                "full_rows_before_sampling": 120000,
            },
        },
        "applied_cleaning": {
            "actions": cleaning_actions,
            "before_rows": 120000,
            "after_rows": 119250,
            "before_cols": 6,
            "after_cols": 6,
        },
        "overview": {
            "n_rows": 119250,
            "n_cols": 6,
            "n_cells": 715500,
            "memory_mb": 18.4,
            "pct_missing_global": 3.2,
            "columns": [
                {
                    "name": "revenue",
                    "semantic_type": "numeric_continuous",
                    "role": "target",
                    "n_unique": 1024,
                    "pct_missing": 0,
                }
            ],
        },
        "data_quality": {
            "missing": {
                "global": {
                    "pct_rows_with_missing": 9.5,
                    "total_missing_cells": 2300,
                    "pct_missing_cells": 3.2,
                    "mean_missing_per_row": 0.18,
                    "median_missing_per_row": 0,
                },
                "ai_comment": "Missing contenuti ma distribuiti su poche colonne.",
            },
            "duplicates": {
                "n_duplicate_rows": 750,
                "pct_duplicate_rows": 0.63,
                "ai_comment": "Duplicati limitati ma non trascurabili.",
            },
        },
        "bivariate": {"num_num": {"ai_comment": "Correlazioni forti concentrate su poche variabili."}},
        "ml_exploratory": {"feature_importance": {"ai_comment": "Revenue guidata da price e quantity."}},
        "inference": {
            "ai_comment": "Diverse feature restano significative dopo correzione FDR.",
            "tests": [
                {
                    "feature": "price",
                    "target": "revenue",
                    "test": "pearson",
                    "pvalue": 0.001,
                    "significant_fdr": True,
                }
            ],
        },
        "univariate": {
            "revenue": {
                "ai_comment": "Distribuzione asimmetrica a destra.",
                "charts": {"hist": {"data": [], "layout": {}}},
            }
        },
        "multivariate": {
            "high_correlation_pairs": [
                {
                    "var_a": "price",
                    "var_b": "margin_pct",
                    "correlation": 0.87,
                    "flag": "high",
                }
            ]
        },
        "insights": {"summary": "Il dataset e pronto per una modellazione supervisionata."},
    }

    chart_map = {
        "overview.charts.types_distribution": "chart_0001",
        "data_quality.missing.charts.missing_cooccurrence": "chart_0002",
        "data_quality.missing.charts.missing_pattern_correlation": "chart_0003",
        "data_quality.missing.charts.missing_dendrogram": "chart_0004",
        "univariate.revenue.charts.hist": "chart_0005",
    }

    typst = _generate_typst(analysis_data, Path("."), chart_map)

    assert "Report EDA professionale" in typst
    assert "Executive Summary" in typst
    assert "Decisioni utente" in typst
    assert "Matrice di co-occorrenza dei missing" in typst
    assert "Dendrogramma dei pattern di missing" in typst
    assert "margin\\_pct" in typst
    assert "Rimozione righe duplicate esatte" in typst
    assert "Trim spazi iniziali/finali: city" in typst
    assert "Pipeline" in typst
