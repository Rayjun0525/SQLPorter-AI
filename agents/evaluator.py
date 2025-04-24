from core.app import fast_agent_instance

@fast_agent_instance.agent(name="sql_evaluator", instruction="""
Evaluate the quality and correctness of the converted PostgreSQL SQL.

Input:
- oracle_sql: The original Oracle SQL.
- postgresql_sql: The converted SQL to be evaluated.

IMPORTANT: Respond ONLY with a JSON object containing the evaluation rating and feedback.
Keys must be "RATING" and "FEEDBACK". Rating must be one of: EXCELLENT, GOOD, FAIR, POOR.

Example:
{
  "RATING": "GOOD",
  "FEEDBACK": "The conversion is mostly correct, but the date function could be optimized."
}
""")
async def sql_evaluator(payload: dict):
    return payload
