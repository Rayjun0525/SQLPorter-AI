# agents/converters.py
"""SQL 변환 에이전트(converter_1, converter_2, converter_3)를 정의합니다."""

from core.app import fast_agent_instance

@fast_agent_instance.agent(name="converter_1", instruction="""
Convert the given Oracle SQL to PostgreSQL.
The input payload might contain 'known_transformations' providing helpful rules. Use them where applicable.

**IMPORTANT:** Respond ONLY with a JSON object containing the converted SQL and the applied transformations.
Keys must be "postgresql_sql" and "transformations".
"transformations" must be a list of objects, each with "from", "to", and "context" keys. It's very important.

Example:
{
  "postgresql_sql": "SELECT column1 FROM your_table WHERE condition;",
  "transformations": [
    {"from": "VARCHAR2", "to": "VARCHAR", "context": "column type"},
    {"from": "SYSDATE", "to": "CURRENT_TIMESTAMP", "context": "function call"}
  ]
}
""")
async def converter_1(payload: dict):
    return payload

@fast_agent_instance.agent(name="converter_2", instruction="""
Convert the given Oracle SQL to PostgreSQL.
The input payload might contain 'known_transformations' providing helpful rules. Use them where applicable.

**IMPORTANT:** Respond ONLY with a JSON object containing the converted SQL and the applied transformations.
Keys must be "postgresql_sql" and "transformations".
"transformations" must be a list of objects, each with "from", "to", and "context" keys. It's very important.


Example:
{
  "postgresql_sql": "SELECT column1 FROM your_table WHERE condition;",
  "transformations": [
    {"from": "VARCHAR2", "to": "VARCHAR", "context": "column type"},
    {"from": "SYSDATE", "to": "CURRENT_TIMESTAMP", "context": "function call"}
  ]
}
""")
async def converter_2(payload: dict):
    return payload

@fast_agent_instance.agent(name="converter_3", instruction="""
Convert the given Oracle SQL to PostgreSQL.
The input payload might contain 'known_transformations' providing helpful rules. Use them where applicable.

**IMPORTANT:** Respond ONLY with a JSON object containing the converted SQL and the applied transformations.
Keys must be "postgresql_sql" and "transformations".
"transformations" must be a list of objects, each with "from", "to", and "context" keys. It's very important.


Example:
{
  "postgresql_sql": "SELECT column1 FROM your_table WHERE condition;",
  "transformations": [
    {"from": "VARCHAR2", "to": "VARCHAR", "context": "column type"},
    {"from": "SYSDATE", "to": "CURRENT_TIMESTAMP", "context": "function call"}
  ]
}
""")
async def converter_3(payload: dict):
    return payload
