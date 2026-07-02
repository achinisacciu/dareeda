import polars as pl
import pytest
from pathlib import Path
from backend.eda.modules.enterprise import (
    _quality_decomposition,
    _detect_pii_candidates,
    _class_balance,
    _leakage_risks,
    _fairness_analysis,
    _predictive_prep,
    _advanced_analytics,
    _governance,
    build_enterprise_outputs
)

class MockDataset:
    file_format = "csv"
    filename = "dummy.csv"

@pytest.fixture
def df_basic():
    return pl.DataFrame({
        "age": [20, 30, 40, 25, 60],
        "email": ["a@b.com", "c@d.com", "e@f.com", None, "g@h.com"],
        "income": ["low", "high", "low", "high", "low"],
        "gender": ["M", "F", "F", "M", "M"]
    })

def test_detect_pii_candidates(df_basic):
    candidates = _detect_pii_candidates(df_basic)
    assert len(candidates) > 0
    pii_types = [c["pii_type"] for c in candidates]
    assert "email" in pii_types

def test_class_balance(df_basic):
    balance = _class_balance(df_basic, "income")
    assert balance is not None
    assert balance["target"] == "income"
    assert len(balance["distribution"]) == 2

def test_leakage_risks(df_basic):
    semantic_types = {"age": "numeric_continuous", "email": "id", "income": "categorical_nominal", "gender": "categorical_nominal"}
    risks = _leakage_risks(df_basic, semantic_types, "income")
    # email is ID, so it should be a leakage risk
    assert any(r["column"] == "email" for r in risks)

def test_fairness_analysis(df_basic):
    # Should work for binary classification
    fairness = _fairness_analysis(df_basic, "income", "classification")
    assert fairness["applicable"] is True
    assert any(p["column"] == "gender" for p in fairness["protected_attributes"])

def test_quality_decomposition(df_basic):
    groups = {"numeric_continuous": ["age"]}
    base_results = {
        "data_quality": {
            "missing": {"global": {"pct_missing_cells": 5.0}},
            "duplicates": {"pct_duplicate_rows": 0.0}
        }
    }
    quality = _quality_decomposition(df_basic, groups, base_results)
    assert "dimensions" in quality
    assert quality["total_score"] > 0

def test_build_enterprise_outputs(df_basic):
    semantic_types = {"age": "numeric_continuous", "email": "id", "income": "categorical_nominal", "gender": "categorical_nominal"}
    groups = {"numeric_continuous": ["age"], "id": ["email"], "categorical_nominal": ["income", "gender"]}
    base_results = {}
    
    result = build_enterprise_outputs(
        df_full=df_basic,
        semantic_types=semantic_types,
        groups=groups,
        base_results=base_results,
        dataset=MockDataset(),
        filepath=Path("dummy.csv"),
        target_col="income",
        problem_type="classification",
        accepted_features=[],
        dataset_hash="hash",
        cleaned_export_relpath=None,
        cleaned_export_hash=None,
        sample_relpath=None,
        result_relpath=None,
        runtime_seconds=1.0,
        tool_version="1.0",
        working_dir=Path(".")
    )
    
    assert "front_matter" in result
    assert "executive" in result
    assert "profiling" in result
    assert "predictive_prep" in result
    assert "advanced_analytics" in result
    assert "governance" in result
    assert "deliverables" in result
