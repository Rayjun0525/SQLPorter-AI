import tempfile
from pathlib import Path
from core.knowledge import (
    save_transformations,
    load_transformations,
    format_rules_for_prompt,
    extract_relevant_keys
)

from core.knowledge import TransformationRule, TransformationMetadata

def test_save_and_load_transformation_tree():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "transformations.json"

        rules = [
            TransformationRule(
                from_pattern="SYSDATE",
                to_pattern="CURRENT_TIMESTAMP",
                context="function call",
                metadata=TransformationMetadata(
                    category="functions",
                    description="Date and time functions",
                    complexity="simple",
                    examples=["SELECT SYSDATE FROM dual;"],
                    related_patterns=["CURRENT_DATE", "LOCALTIMESTAMP"]
                )
            ),
            TransformationRule(
                from_pattern="NVL",
                to_pattern="COALESCE",
                context="function call",
                metadata=TransformationMetadata(
                    category="functions",
                    description="Null handling functions",
                    complexity="simple",
                    examples=["SELECT NVL(col, 0) FROM table;"],
                    related_patterns=["NULLIF", "COALESCE"]
                )
            )
        ]

        save_transformations(rules, file_path=path)
        loaded = load_transformations(file_path=path)

        assert "functions" in loaded
        assert "SYSDATE" in loaded["functions"]
        assert len(loaded["functions"]["SYSDATE"]) == 1
        assert loaded["functions"]["SYSDATE"][0].to_pattern == "CURRENT_TIMESTAMP"
        assert "NVL" in loaded["functions"]

def test_no_duplicates_on_save():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "transformations.json"
        rule = TransformationRule(
            from_pattern="SYSDATE",
            to_pattern="CURRENT_TIMESTAMP",
            context="function call",
            metadata=TransformationMetadata(
                category="functions",
                description="Date and time functions",
                complexity="simple",
                examples=["SELECT SYSDATE FROM dual;"],
                related_patterns=["CURRENT_DATE", "LOCALTIMESTAMP"]
            )
        )

        save_transformations([rule], file_path=path)
        save_transformations([rule], file_path=path)  # try saving duplicate
        loaded = load_transformations(file_path=path)

        assert len(loaded["functions"]["SYSDATE"]) == 1  # should not duplicate

def test_format_rules_for_prompt_and_key_extraction():
    tree = {
        "functions": {
            "SYSDATE": [
                TransformationRule(
                    from_pattern="SYSDATE",
                    to_pattern="CURRENT_TIMESTAMP",
                    context="function call",
                    metadata=TransformationMetadata(
                        category="functions",
                        description="Date and time functions",
                        complexity="simple",
                        examples=["SELECT SYSDATE FROM dual;"],
                        related_patterns=["CURRENT_DATE", "LOCALTIMESTAMP"]
                    )
                )
            ],
            "NVL": [
                TransformationRule(
                    from_pattern="NVL",
                    to_pattern="COALESCE",
                    context="function call",
                    metadata=TransformationMetadata(
                        category="functions",
                        description="Null handling functions",
                        complexity="simple",
                        examples=["SELECT NVL(col, 0) FROM table;"],
                        related_patterns=["NULLIF", "COALESCE"]
                    )
                )
            ]
        }
    }
    sql_text = "SELECT NVL(col, 0), SYSDATE FROM DUAL;"
    keys = extract_relevant_keys(sql_text, ["SYSDATE", "NVL"])

    assert "SYSDATE" in keys
    assert "NVL" in keys

    formatted = format_rules_for_prompt(tree, keys)
    assert "Category: functions" in formatted
    assert "Description: Date and time functions" in formatted
    assert "SYSDATE -> CURRENT_TIMESTAMP" in formatted
    assert "NVL -> COALESCE" in formatted
