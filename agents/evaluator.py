from core.app import fast_agent_instance
from config.loader import load_sqlporter_config
from mcp_agent.llm.augmented_llm import RequestParams

sqlporter_config = load_sqlporter_config()
settings_config = sqlporter_config.get("settings", {})
max_tokens = settings_config.get("max_tokens", 10000)

@fast_agent_instance.agent(name="sql_evaluator", instruction="""
You are a SQL evaluator who verifies semantic equivalence and conversion quality between Oracle SQL and PostgreSQL SQL.

You will receive:
- "oracle_sql": the original Oracle SQL query
- "postgresql_sql": the converted PostgreSQL SQL query

Your job is to:
1. Determine whether the PostgreSQL query is **semantically equivalent** to the Oracle one.
2. Check if the conversion is accurate, idiomatic, and avoids Oracle-specific artifacts.
3. Identify any potential mismatches in logic, function behavior, default values, or types.

Respond ONLY with a valid JSON object:
{
  "RATING": "EXCELLENT" | "GOOD" | "FAIR" | "POOR",
  "FEEDBACK": "<short but precise feedback explaining any mismatches or confirming equivalence>"
}

Examples:
{
  "RATING": "GOOD",
  "FEEDBACK": "The general logic is preserved, but Oracle's NVL was not fully replaced with COALESCE."
}
""",  request_params=RequestParams(maxTokens=max_tokens),)
async def sql_evaluator(payload: dict):
    return payload