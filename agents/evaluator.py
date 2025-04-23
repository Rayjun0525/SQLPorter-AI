# agents/evaluator.py
"""SQL 평가 에이전트(sql_evaluator)를 정의합니다."""

from core.app import fast_agent_instance

@fast_agent_instance.agent(name="sql_evaluator", instruction="""
Evaluate the quality and correctness of the converted PostgreSQL SQL.

Given:
- oracle_sql: the original Oracle SQL
- postgresql_sql: the converted SQL to be evaluated

**IMPORTANT:** Respond ONLY with a JSON object containing the evaluation rating and feedback.
Keys should be "RATING" and "FEEDBACK". Rating must be one of: EXCELLENT, GOOD, FAIR, POOR.

Example:
{
  "RATING": "GOOD",
  "FEEDBACK": "The conversion is mostly correct, but the date function could be optimized."
}
""")
async def sql_evaluator(payload: dict):
    # fast-agent 프레임워크가 페이로드 처리를 담당하므로 그대로 반환
    return payload
