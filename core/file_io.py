# core/file_io.py

"""
🔹 현재 작업: 파일 입출력 처리기 구성
파일: core/file_io.py
목표:
    - ASIS/ 폴더에서 SQL 파일 읽기
    - TOBE/ 폴더에 결과 SQL 저장 (주석 포함)
    - 변환 결과 리포트 저장

다음 단계 예고: main.py 구성 (전체 실행 진입점)
"""

from pathlib import Path
from typing import List
import json

def get_sql_files(input_dir: str) -> List[Path]:
    return sorted(Path(input_dir).glob("*.sql"))

def read_sql_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")

def write_sql_with_comment(output_path: Path, sql: str, comment: str, prefix: str = "--"):
    comment_block = f"{prefix} {comment.strip().replace('\n', f'\n{prefix} ')}\n\n"
    output_path.write_text(comment_block + sql, encoding="utf-8")

def write_report(report_path: Path, result_dict: dict):
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
