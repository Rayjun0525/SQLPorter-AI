# agents/evaluator.py

"""
🔹 현재 작업: 평가 에이전트 정의
파일: agents/evaluator.py
목표: 변환된 PostgreSQL SQL의 품질을 평가하는 agent 정의

다음 단계 예고: agents/pipeline.py 작성 (정교화 루프 evaluator_optimizer 구성)
"""

from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("SQL Evaluation Agent")

@fast.agent(name="sql_evaluator", instruction="""
Evaluate the quality and correctness of the converted PostgreSQL SQL.

Given:
- oracle_sql: the original Oracle SQL
- postgresql_sql: the converted SQL to be evaluated

Respond ONLY in the following format:
RATING: <EXCELLENT | GOOD | FAIR | POOR>
FEEDBACK: <explanation of any issues or improvements>
""")
async def sql_evaluator(payload: dict):
    return payload
