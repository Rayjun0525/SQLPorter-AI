from core.app import fast_agent_instance
from config.loader import load_sqlporter_config
from mcp_agent.llm.augmented_llm import RequestParams

# Load configuration
sqlporter_config = load_sqlporter_config()
models_config = sqlporter_config.get("models", {})
instructions_config = sqlporter_config.get("instructions", {})
settings_config = sqlporter_config.get("settings", {})
max_tokens = settings_config.get("max_tokens", 10000)

DEFAULT_INSTRUCTION = """
Convert the given Oracle SQL to PostgreSQL.

You will also receive a list of known transformation rules under the key "known_transformations".
These rules represent validated mappings from Oracle to PostgreSQL syntax.
You MUST actively consult and apply relevant rules from this list wherever applicable.
Do NOT ignore them. They are authoritative.

**CRITICAL**: Respond **ONLY** with a JSON object containing the converted SQL and the applied transformations. **No other output is allowed**, including comments, explanations, or wrapping in triple backticks (e.g., ```json). Return **raw JSON text only** in the exact format specified below.

**Required Keys**:
- "postgresql_sql": The converted PostgreSQL query as a string.
- "transformations": A list of objects, each with **exactly** these keys: "from", "to", and "context" (no additional keys allowed).

**Format Requirements**:
- Ensure the JSON is valid and strictly follows the structure shown in the example.
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

def register(name, model_name, instruction_text):
    @fast_agent_instance.agent(name=name, model=model_name, instruction=instruction_text, request_params=RequestParams(maxTokens=max_tokens),)
    async def converter(payload: dict):
        return payload

# Register all converters using loop
for agent_name in models_config:
    model = models_config.get(agent_name)
    custom_instruction = instructions_config.get(agent_name, "")

    if custom_instruction:
        instruction = f"{DEFAULT_INSTRUCTION.strip()}\n\n{custom_instruction.strip()}"
    else:
        instruction = DEFAULT_INSTRUCTION

    register(agent_name, model, instruction)
