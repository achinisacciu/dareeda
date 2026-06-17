# Categoria: unit
# File sorgente: backend/core/report_generator.py
# Creato: 2026-06-14
# Aggiornato: 2026-06-14

from core.report_generator import (
    _bullet_list,
    _cleaning_rows,
    _collect_summary_insights,
    _esc,
    _fmt_float,
    _fmt_int,
    _format_cleaning_actions,
    _img,
    _pair_table,
    _rows_table,
)


def test_esc_escapes_special_chars():
    assert "\\[" in _esc("[test]")
    assert "\\*" in _esc("*star*")
    assert "\\#" in _esc("#hash")
    assert "\\@" in _esc("@mention")
    assert _esc(None) == ""


def test_fmt_int_formats_with_dot_separator():
    assert _fmt_int(1000) == "1.000"
    assert _fmt_int(999) == "999"
    assert _fmt_int("abc") == "0"


def test_fmt_float_formats_two_decimals():
    assert _fmt_float(3.14159) == "3.14"
    assert _fmt_float(10.0, suffix="%") == "10.00%"
    assert _fmt_float("bad") == "0"


def test_img_returns_figure_string():
    result = _img("charts/fig1.png", "My Chart", width="80%")
    assert "image(" in result
    assert "My Chart" in result
    assert 'width: 80%' in result


def test_bullet_list_returns_items():
    items = ["Item 1", "Item 2", "Item 3"]
    result = _bullet_list(items)
    assert "- Item 1" in result
    assert "- Item 2" in result
    assert "- Item 3" in result


def test_bullet_list_returns_empty_label_when_no_items():
    result = _bullet_list([])
    assert "Nessun elemento rilevante" in result


def test_pair_table_formats_cells():
    rows = [("Label1", "Value1"), ("Label2", "Value2")]
    result = _pair_table(rows)
    assert "Label1" in result
    assert "Value1" in result
    assert "table.cell" in result


def test_pair_table_pads_odd_rows():
    rows = [("Label1", "Value1")]
    result = _pair_table(rows)
    assert "table.cell" in result


def test_rows_table_formats_table():
    items = [
        {"name": "A", "value": "1"},
        {"name": "B", "value": "2"},
    ]
    keys = [("Name", "name"), ("Value", "value")]
    result = _rows_table(items, keys)
    assert "table" in result
    assert "Name" in result
    assert "Value" in result


def test_rows_table_returns_empty_when_no_items():
    result = _rows_table([], [("Name", "name")])
    assert "Nessun dato disponibile" in result


def test_rows_table_respects_limit():
    items = [{"name": f"Item{i}", "value": str(i)} for i in range(20)]
    keys = [("Name", "name")]
    result = _rows_table(items, keys, limit=5)
    assert result.count("Item") == 5


def test_format_cleaning_actions_formats_known_types():
    actions = [
        {"type": "exclude_column", "column": "col1", "params": {}},
        {"type": "drop_duplicate_rows", "column": None, "params": {}},
        {"type": "replace_values", "column": "col2", "params": {"values": ["a", "b"]}},
        {"type": "trim_whitespace", "column": "col3", "params": {}},
    ]
    result = _format_cleaning_actions(actions)
    assert len(result) == 4
    assert "col1" in result[0]
    assert "col2" in result[2]
    assert "col3" in result[3]


def test_format_cleaning_actions_handles_empty():
    assert _format_cleaning_actions([]) == []
    assert _format_cleaning_actions(None) == []


def test_collect_summary_insights_dedupes():
    data = {
        "data_quality": {"missing": {"ai_comment": "Missing insight"}, "duplicates": {"ai_comment": "Missing insight"}},
        "insights": {"summary": "Summary", "ai_comment": "AI comment", "headline": "Headline"},
    }
    result = _collect_summary_insights(data)
    assert "Missing insight" in result
    assert result.count("Missing insight") == 1
    assert "Summary" in result
    assert len(result) <= 8


def test_collect_summary_insights_returns_empty_for_empty_data():
    assert _collect_summary_insights({}) == []


def test_cleaning_rows_formats_actions():
    actions = [
        {"type": "exclude_column", "column": "id", "params": {}},
        {"type": "drop_duplicate_rows", "column": None, "params": {}},
    ]
    result = _cleaning_rows(actions)
    assert len(result) == 2
    assert result[0]["action"] == "exclude_column"
    assert result[0]["column"] == "id"
