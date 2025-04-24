import tempfile
from pathlib import Path
from core.file_io import get_sql_files, read_sql_file, write_sql_with_comment

def test_read_and_write_sql_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir)
        input_dir = base / "ASIS"
        output_dir = base / "TOBE"
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)

        # Create test input SQL file
        original_sql = "SELECT * FROM employees;"
        sql_file = input_dir / "test_query.sql"
        sql_file.write_text(original_sql, encoding="utf-8")

        # Write with comment
        write_sql_with_comment(
            output_base_dir=output_dir,
            input_base_dir=input_dir,
            input_path=sql_file,
            sql=original_sql,
            comment="Converted from: test_query.sql",
            prefix="--"
        )

        # Check result file
        result_file = output_dir / "test_query_ported.sql"
        assert result_file.exists()
        result_content = result_file.read_text(encoding="utf-8")
        assert original_sql in result_content
        assert "-- Converted from: test_query.sql" in result_content

def test_recursive_sql_discovery():
    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir)
        sub_dir = base / "ASIS" / "project" / "subfolder"
        sub_dir.mkdir(parents=True)

        file1 = sub_dir / "a.sql"
        file2 = base / "ASIS" / "b.sql"
        file1.write_text("SELECT 1;", encoding="utf-8")
        file2.write_text("SELECT 2;", encoding="utf-8")

        found_files = get_sql_files(base / "ASIS")
        found_names = sorted([f.name for f in found_files])

        assert found_names == ["a.sql", "b.sql"]
