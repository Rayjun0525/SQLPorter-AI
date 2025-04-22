# core/runner.py

"""
🔹 현재 작업: 실행 로직 구성
파일: core/runner.py
목표: 설정(config) 기반으로 에이전트를 순차적으로 호출하는 워크플로우 구성
    - 병렬 변환 실행
    - 병합 및 평가 루프
    - 결과 저장은 file_io.py에서 분리 예정

다음 단계 예고: core/file_io.py 작성 (SQL 파일 읽기/쓰기, 주석 추가 등)
"""

from typing import List
from mcp_agent.core.fastagent import FastAgent

from config.loader import load_sqlporter_config

fast = FastAgent("SQLPorter Runner")

async def run_parallel_conversion(agent, oracle_sql: str, model_map: dict) -> List[str]:
    payload = {"oracle_sql": oracle_sql}
    results = []
    for agent_name, model in model_map.items():
        result = await agent[agent_name].send(payload, model=model)
        results.append(result)
    return results

async def run_pipeline(agent, oracle_sql: str, model_map: dict) -> str:
    candidates = await run_parallel_conversion(agent, oracle_sql, model_map)

    merged = await agent.merge_and_select.send({
        "oracle_sql": oracle_sql,
        "candidates": candidates
    })

    final = await agent.oracle_to_pg_pipeline.send({
        "oracle_sql": oracle_sql,
        "postgresql_sql": merged
    })

    return final

async def run_single_sql(agent, config: dict, oracle_sql: str) -> str:
    model_map = config["models"]
    result_sql = await run_pipeline(agent, oracle_sql, model_map)
    return result_sql
