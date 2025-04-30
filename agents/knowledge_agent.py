from core.app import fast_agent_instance
from core.knowledge import load_transformations, save_transformations
from typing import List, Dict

@fast_agent_instance.agent(name="knowledge_manager", instruction="""
You are an expert in SQL dialects and responsible for auditing and cleaning transformation knowledge for Oracle-to-PostgreSQL SQL conversion.

You will receive a JSON input with:
- "action": always "audit"
- "rules": a list of transformation rules. Each rule contains:
    - "from": an Oracle SQL expression or keyword
    - "to": the PostgreSQL equivalent
    - "context": where or how the rule applies (optional)
    - "example": example of usage (optional)

Your tasks:
1. Remove invalid or meaningless rules:
   - Missing or empty 'from' or 'to'
   - 'from' and 'to' are identical
   - 'to' still contains Oracle-specific expressions or invalid PostgreSQL
2. Detect and remove duplicate rules (same 'from', 'to', and 'context')
3. If 'to' is not a valid PostgreSQL expression, recommend a fix

Respond ONLY with a valid JSON object:
{
  "cleaned_rules": [ ... ],         // list of cleaned rules
  "removed_count": <int>,           // number of rules removed
  "issues": [                       // list of issues detected
    {
      "index": <int>,               // index in original input
      "reason": "<why removed>",
      "suggestion": "<if fixable>"  // optional
    }
  ]
}
""")
async def knowledge_manager(payload: dict):
    rules: List[Dict] = payload.get("rules", [])
    cleaned = []
    seen = set()
    issues = []

    for i, rule in enumerate(rules):
        f = rule.get("from", "").strip()
        t = rule.get("to", "").strip()
        c = rule.get("context", "").strip()
        ex = rule.get("example", "").strip()
        key = (f.lower(), t.lower(), c.lower())

        # Validation
        if not f or not t:
            issues.append({"index": i, "reason": "Missing 'from' or 'to'"})
            continue
        if f == t:
            issues.append({"index": i, "reason": "'from' and 'to' are identical"})
            continue
        if key in seen:
            issues.append({"index": i, "reason": "Duplicate rule"})
            continue

        # Allow AI model to reason about suspicious "to" values — offloaded to LLM
        # Here we retain the rule unless obvious problems are present.
        seen.add(key)
        cleaned.append({"from": f, "to": t, "context": c, "example": ex})

    return {
        "cleaned_rules": cleaned,
        "removed_count": len(rules) - len(cleaned),
        "issues": issues
    }
