from pathlib import Path
from typing import List
import json
import sys

def get_sql_files(input_dir: Path) -> List[Path]:
    """Recursively collect all .sql files from the input directory."""
    if not input_dir.is_dir():
        print(f"Error: '{input_dir}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)
    return sorted(input_dir.rglob("*.sql"))

def read_sql_file(file_path: Path) -> str:
    """Read the content of a SQL file as a string."""
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file ({file_path}): {e}", file=sys.stderr)
        sys.exit(1)

def write_sql_with_comment(output_base_dir: Path, input_base_dir: Path, input_path: Path, sql: str, comment: str, prefix: str = "--"):
    """
    Write the converted SQL with a header comment to the output path.
    The output path mirrors the input directory structure and appends '_ported' to the filename.
    """
    relative_path = input_path.relative_to(input_base_dir)
    output_path = output_base_dir / relative_path.with_name(relative_path.stem + "_ported.sql")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        comment_block = f"{prefix} {comment.strip().replace('\n', f'\n{prefix} ')}\n\n"
        output_path.write_text(comment_block + sql, encoding="utf-8")
    except IOError as e:
        print(f"Error writing file ({output_path}): {e}", file=sys.stderr)
        sys.exit(1)

def write_report(report_path: Path, result_dict: dict):
    """Write the result summary dictionary to a JSON report file."""
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error writing report file ({report_path}): {e}", file=sys.stderr)
        sys.exit(1)

def write_html_report(report_path: Path, result_dict: dict):
    """Generate a simple HTML report from the result dictionary."""
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        rows = ""
        for filename, data in result_dict.items():
            status = data.get("status", "")
            error = data.get("error", "")
            rating = data.get("rating", "")
            feedback = data.get("feedback", "")
            rows += f"""
            <tr>
                <td>{filename}</td>
                <td>{status}</td>
                <td>{error}</td>
                <td>{rating}</td>
                <td>{feedback}</td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>SQLPorter Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
                th {{ background-color: #f4f4f4; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h2>SQLPorter Result Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Status</th>
                        <th>Error</th>
                        <th>Rating</th>
                        <th>Feedback</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
        </html>
        """

        html_path = report_path.with_suffix(".html")
        html_path.write_text(html_content, encoding="utf-8")
        print(f"HTML report generated at {html_path}")

    except IOError as e:
        print(f"Error writing HTML report: {e}", file=sys.stderr)
