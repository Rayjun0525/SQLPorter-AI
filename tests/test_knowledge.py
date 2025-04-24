import tempfile
from pathlib import Path
from core.knowledge import (
    save_transformations,
    load_transformations,
    format_rules_for_prompt,
    extract_relevant_keys
)

def test_save_and_load_transformation_tree():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "transformations.json"

        rules = [
            {"from": "SYSDATE", "to": "CURRENT_TIMESTAMP", "context": "function call", "example": "SELECT SYSDATE FROM dual;"},
            {"from": "NVL", "to": "COALESCE", "context": "function call"}
        ]

        save_transformations(rules, file_path=path)
        loaded = load_transformations(file_path=path)

        assert "SYSDATE" in loaded
        assert len(loaded["SYSDATE"]) == 1
        assert loaded["SYSDATE"][0]["to"] == "CURRENT_TIMESTAMP"
        assert "NVL" in loaded

def test_no_duplicates_on_save():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "transformations.json"
        rule = {"from": "SYSDATE", "to": "CURRENT_TIMESTAMP", "context": "function call"}

        save_transformations([rule], file_path=path)
        save_transformations([rule], file_path=path)  # try saving duplicate
        loaded = load_transformations(file_path=path)

        assert len(loaded["SYSDATE"]) == 1  # should not duplicate

def test_format_rules_for_prompt_and_key_extraction():
    tree = {
        "SYSDATE": [{"to": "CURRENT_TIMESTAMP", "context": "function call", "example": "SELECT SYSDATE FROM dual;"}],
        "NVL": [{"to": "COALESCE", "context": "function call"}]
    }
    sql_text = "SELECT NVL(col, 0), SYSDATE FROM DUAL;"
    keys = extract_relevant_keys(sql_text, list(tree.keys()))

    assert "SYSDATE" in keys
    assert "NVL" in keys

    formatted = format_rules_for_prompt(tree, keys)
    assert "SYSDATE -> CURRENT_TIMESTAMP" in formatted
    assert "NVL -> COALESCE" in formatted
