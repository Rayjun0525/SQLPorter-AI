from core.app import fast_agent_instance
from config.loader import load_sqlporter_config
from mcp_agent.llm.augmented_llm import RequestParams

sqlporter_config = load_sqlporter_config()
settings_config = sqlporter_config.get("settings", {})
max_tokens = settings_config.get("max_tokens", 10000)

@fast_agent_instance.agent(name="merge_and_select", instruction="""
Given the original Oracle SQL and multiple candidate PostgreSQL conversions,
merge the best parts of the candidates and select the best final PostgreSQL SQL.
Also, report the transformation rules applied in the final selected SQL.

Input:
- oracle_sql: The original Oracle SQL query.
- candidates: A list of PostgreSQL SQL strings converted by different agents.

IMPORTANT: Respond ONLY with a JSON object containing the best merged/selected PostgreSQL SQL string and the applied transformations.
Keys must be "postgresql_sql" and "transformations".
"transformations" must be a list of objects, each with "from", "to", and "context" keys.

Example:
{
  "postgresql_sql": "SELECT final_column FROM final_table WHERE COALESCE(col2, 'default');",
  "transformations": [
    {"from": "VARCHAR2", "to": "VARCHAR", "context": "column type in final_column"},
    {"from": "NVL", "to": "COALESCE", "context": "function call in WHERE clause"}
  ]
}
""",  request_params=RequestParams(maxTokens=max_tokens),)
async def merge_and_select(payload: dict):
    return payload
