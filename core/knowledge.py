import json
from pathlib import Path
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

DEFAULT_KNOWLEDGE_DIR = Path("./knowledge")
DEFAULT_KNOWLEDGE_FILE = DEFAULT_KNOWLEDGE_DIR / "transformations.json"

def load_transformations(file_path: Path = DEFAULT_KNOWLEDGE_FILE) -> Dict[str, List[Dict[str, str]]]:
    """Load the transformation rules as a dictionary tree."""
    if not file_path.exists():
        logger.info(f"Knowledge file not found: {file_path}. Returning empty tree.")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            else:
                logger.warning(f"Invalid format in knowledge file: expected dict.")
                return {}
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error loading knowledge: {e}", exc_info=True)
        return {}

def save_transformations(new_rules: List[Dict[str, str]], file_path: Path = DEFAULT_KNOWLEDGE_FILE):
    """Save new transformation rules into the knowledge tree."""
    if not new_rules:
        return

    DEFAULT_KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    existing_tree = load_transformations(file_path)
    added_count = 0

    for rule in new_rules:
        from_pattern = rule.get("from")
        to_pattern = rule.get("to")
        context = rule.get("context", "unknown")
        example = rule.get("example", "")

        if not from_pattern or not to_pattern:
            continue

        entry = {"to": to_pattern, "context": context, "example": example}
        entries = existing_tree.setdefault(from_pattern, [])
        if not any(e["to"] == to_pattern and e["context"] == context for e in entries):
            entries.append(entry)
            added_count += 1

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_tree, f, indent=2, ensure_ascii=False)
        logger.info(f"{added_count} new transformation(s) saved to knowledge base.")
    except IOError as e:
        logger.error(f"Error saving knowledge: {e}", exc_info=True)

def format_rules_for_prompt(tree: Dict[str, List[Dict[str, str]]], relevant_keys: List[str]) -> str:
    """Format a subset of transformation rules for inclusion in a prompt."""
    prompt_lines = ["Here are relevant transformation rules:"]
    for key in relevant_keys:
        if key not in tree:
            continue
        for rule in tree[key]:
            line = f"- {key} -> {rule['to']} (ctx: {rule.get('context')})"
            if rule.get("example"):
                line += f" e.g. {rule['example']}"
            prompt_lines.append(line)
    return "\n".join(prompt_lines)

def extract_relevant_keys(sql_text: str, known_keys: List[str]) -> List[str]:
    """Find transformation keys that are present in the given SQL text."""
    upper_sql = sql_text.upper()
    return [k for k in known_keys if k.upper() in upper_sql]
