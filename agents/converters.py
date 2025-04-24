from core.app import fast_agent_instance
from config.loader import load_sqlporter_config

# Load configuration
sqlporter_config = load_sqlporter_config()
models_config = sqlporter_config.get("models", {})
instructions_config = sqlporter_config.get("instructions", {})

DEFAULT_INSTRUCTION = """
Convert the given Oracle SQL to PostgreSQL.
The input payload might contain 'known_transformations' providing helpful rules. Use them where applicable.

IMPORTANT: Respond ONLY with a JSON object containing the converted SQL and the applied transformations.
Keys must be "postgresql_sql" and "transformations".
"transformations" must be a list of objects, each with "from", "to", and "context" keys.

Example:
{
  "postgresql_sql": "SELECT column1 FROM your_table WHERE condition;",
  "transformations": [
    {"from": "VARCHAR2", "to": "VARCHAR", "context": "column type"},
    {"from": "SYSDATE", "to": "CURRENT_TIMESTAMP", "context": "function call"}
  ]
}
"""

# Register all converters using loop
for agent_name in ["converter_1", "converter_2", "converter_3"]:
    model = models_config.get(agent_name)
    instruction = instructions_config.get(agent_name, DEFAULT_INSTRUCTION)

    def register(name, model_name, instruction_text):
        @fast_agent_instance.agent(name=name, model=model_name, instruction=instruction_text)
        async def converter(payload: dict):
            return payload
        return converter

    register(agent_name, model, instruction)
