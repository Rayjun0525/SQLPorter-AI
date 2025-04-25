from core.app import fast_agent_instance
from config.loader import load_sqlporter_config

# Load configuration
sqlporter_config = load_sqlporter_config()
models_config = sqlporter_config.get("models", {})
instructions_config = sqlporter_config.get("instructions", {})

DEFAULT_INSTRUCTION = """
Convert the given Oracle SQL to PostgreSQL.
**CRITICAL**: Respond **ONLY** with a JSON object containing the converted SQL and the applied transformations. **No other output is allowed**, including comments, explanations, or wrapping in triple backticks (e.g., ```json). Return **raw JSON text only** in the exact format specified below.

**Required Keys**:
- "postgresql_sql": The converted PostgreSQL query as a string.
- "transformations": A list of objects, each with **exactly** these keys: "from", "to", and "context" (no additional keys allowed).

**Format Requirements**:
- Ensure the JSON is valid and strictly follows the structure shown in the example.
- Do **NOT** include any extra fields, wrappers, or formatting outside the JSON object.
- The "transformations" list must include all applied changes, with each object describing one transformation.

**Example**:
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
    custom_instruction = instructions_config.get(agent_name)
    
    if custom_instruction:
        instruction = f"{DEFAULT_INSTRUCTION.strip()}\n\n{custom_instruction.strip()}"
    else:
        instruction = DEFAULT_INSTRUCTION

    def register(name, model_name, instruction_text):
        @fast_agent_instance.agent(name=name, model=model_name, instruction=instruction_text)
        async def converter(payload: dict):
            return payload
        return converter

    register(agent_name, model, instruction)
