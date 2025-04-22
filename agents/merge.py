# agents/merge.py

"""
🔹 현재 작업: 병합/선택 에이전트 정의
파일: agents/merge.py
목표: 여러 변환 후보 중 최적 또는 병합된 결과를 선택하는 agent 정의

다음 단계 예고: agents/evaluator.py 작성 (PostgreSQL SQL 평가 agent)
"""

from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("SQL Merge Agent")

@fast.agent(name="merge_and_select", instruction="""
Given:
- oracle_sql: the original Oracle SQL query
- candidates: a list of converted PostgreSQL SQL queries

Evaluate:
- Which candidate best preserves the original intent?
- Optionally, merge the strengths of each.

Respond ONLY with the final, selected PostgreSQL SQL.
""")
async def merge_and_select(payload: dict):
    return payload
