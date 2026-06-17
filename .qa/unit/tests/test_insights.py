# Categoria: unit
# File sorgente: backend/eda/modules/insights.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

from eda.modules.insights import run


def test_insights_returns_expected_structure():
    result = run(None, None, {}, {})
    assert "generated" in result
    assert result["generated"] is True
    assert "note" in result
    assert isinstance(result["note"], str)
    assert len(result["note"]) > 0
