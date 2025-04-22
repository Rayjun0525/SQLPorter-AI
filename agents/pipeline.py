# agents/pipeline.py

"""
🔹 현재 작업: 정교화 루프 워크플로우 정의
파일: agents/pipeline.py
목표: evaluator-optimizer 구성
    - generator: merge_and_select
    - evaluator: sql_evaluator

다음 단계 예고: core/runner.py 작성 (전체 실행 흐름 조립)
"""

from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("SQL Evaluation Pipeline")

@fast.evaluator_optimizer(
    name="oracle_to_pg_pipeline",
    generator="merge_and_select",
    evaluator="sql_evaluator",
    min_rating="EXCELLENT",
    max_refinements=3
)
async def oracle_to_pg_pipeline(payload: dict):
    return payload
