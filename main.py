# main.py

"""
🔹 현재 작업: 실행 진입점 구성
파일: main.py
목표:
    - 설정 로딩
    - FastAgent 실행 컨텍스트 열기
    - 입력 폴더의 모든 SQL 파일을 순회하며 변환 수행

💡 실행: uv run main.py
"""

import asyncio
from pathlib import Path
from config.loader import load_sqlporter_config
from core.runner import run_single_sql
from core.file_io import get_sql_files, read_sql_file, write_sql_with_comment, write_report
from mcp_agent.core.fastagent import FastAgent

async def main():
    config = load_sqlporter_config()
    input_dir = Path(config["paths"]["input_dir"])
    output_dir = Path(config["paths"]["output_dir"])
    report_dir = Path(config["paths"]["report_dir"])
    prefix = config["settings"].get("comment_prefix", "--")

    output_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)

    fast = FastAgent("SQLPorter Main")

    summary = {}

    async with fast.run() as agent:
        for sql_path in get_sql_files(input_dir):
            try:
                oracle_sql = read_sql_file(sql_path)
                result_sql = await run_single_sql(agent, config, oracle_sql)

                comment = f"Converted from: {sql_path.name}"
                out_path = output_dir / sql_path.name
                write_sql_with_comment(out_path, result_sql, comment, prefix)

                summary[sql_path.name] = {"status": "success"}
            except Exception as e:
                summary[sql_path.name] = {"status": "error", "message": str(e)}

    write_report(report_dir / "result_summary.json", summary)
    print("✅ 변환 완료. 리포트 생성됨.")

if __name__ == "__main__":
    asyncio.run(main())