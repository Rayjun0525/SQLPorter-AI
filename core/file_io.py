# core/file_io.py
"""파일 입출력 관련 유틸리티 함수들을 제공합니다."""

from pathlib import Path
from typing import List
import json
import sys # 에러 출력을 위해 추가

def get_sql_files(input_dir: str) -> List[Path]:
    """지정된 디렉토리에서 .sql 파일 목록을 찾아 정렬하여 반환합니다."""
    input_path = Path(input_dir)
    if not input_path.is_dir():
        print(f"❌ 입력 디렉토리 '{input_dir}'를 찾을 수 없거나 디렉토리가 아닙니다.", file=sys.stderr)
        sys.exit(1) # 오류 발생 시 종료
    return sorted(input_path.glob("*.sql"))

def read_sql_file(file_path: Path) -> str:
    """SQL 파일을 읽어 내용을 문자열로 반환합니다."""
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"❌ 파일 읽기 오류 ({file_path}): {e}", file=sys.stderr)
        sys.exit(1)

def write_sql_with_comment(output_path: Path, sql: str, comment: str, prefix: str = "--"):
    """SQL 내용과 주석을 함께 파일에 작성합니다."""
    try:
        # 부모 디렉토리가 없으면 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)
        comment_block = f"{prefix} {comment.strip().replace('\n', f'\n{prefix} ')}\n\n"
        output_path.write_text(comment_block + sql, encoding="utf-8")
    except IOError as e:
        print(f"❌ 파일 쓰기 오류 ({output_path}): {e}", file=sys.stderr)
        sys.exit(1)

def write_report(report_path: Path, result_dict: dict):
    """결과 딕셔너리를 JSON 형식으로 리포트 파일에 작성합니다."""
    try:
        # 부모 디렉토리가 없으면 생성
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"❌ 리포트 파일 쓰기 오류 ({report_path}): {e}", file=sys.stderr)
        sys.exit(1)

