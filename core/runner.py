import asyncio
import logging
import json
from typing import List, Dict, Any

import core.knowledge

logger = logging.getLogger(__name__)

def looks_like_sql(s: str) -> bool:
    s_upper = s.strip().upper()
    return s_upper.startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'WITH', '--', '/*'))

def process_agent_result(result_data: Any, agent_name: str) -> Dict | None:
    processed_dict = None

    if isinstance(result_data, dict):
        processed_dict = result_data
    elif isinstance(result_data, str):
        stripped_res = result_data.strip()
        if stripped_res.startswith('{') and stripped_res.endswith('}'):
            try:
                parsed_json = json.loads(stripped_res)
                if isinstance(parsed_json, dict):
                    processed_dict = parsed_json
                    logger.info(f"Agent '{agent_name}' returned valid JSON.")
            except json.JSONDecodeError:
                logger.warning(f"Agent '{agent_name}' failed JSON decode.")
        elif looks_like_sql(stripped_res):
            processed_dict = {"postgresql_sql": stripped_res}
        else:
            logger.warning(f"Agent '{agent_name}' returned an unrecognized string.")
    else:
        logger.warning(f"Agent '{agent_name}' returned unexpected type {type(result_data)}")

    if processed_dict and "postgresql_sql" in processed_dict:
        processed_dict["agent_name"] = agent_name
        processed_dict.setdefault("transformations", [])
        return processed_dict
    elif processed_dict:
        logger.warning(f"Missing 'postgresql_sql' in result from '{agent_name}'.")
        return None
    return None

async def run_parallel_conversion(agent: Any, config: Dict, oracle_sql: str, model_map: Dict[str, str]) -> List[Dict]:
    payload = {"oracle_sql": oracle_sql}
    initial_tasks = []
    executed_agent_names = []

    tree = core.knowledge.load_transformations()
    relevant_keys = core.knowledge.extract_relevant_keys(oracle_sql, list(tree.keys()))
    formatted_knowledge = core.knowledge.format_rules_for_prompt(tree, relevant_keys)
    payload["known_transformations"] = formatted_knowledge

    for agent_name in model_map:
        try:
            agent_instance = agent[agent_name]
            initial_tasks.append(agent_instance.send(payload))
            executed_agent_names.append(agent_name)
        except Exception as e:
            logger.error(f"Failed to prepare task for '{agent_name}': {e}", exc_info=True)

    if not initial_tasks:
        return [{"error": "No valid conversion agents found"}]

    initial_results = await asyncio.gather(*initial_tasks, return_exceptions=True)
    processed_results = [None] * len(executed_agent_names)
    agents_to_retry = []

    for i, res in enumerate(initial_results):
        agent_name = executed_agent_names[i]
        processed = None
        error_for_retry = None

        if isinstance(res, Exception):
            logger.warning(f"Agent '{agent_name}' failed with exception: {res}")
            error_for_retry = str(res)
        else:
            processed = process_agent_result(res, agent_name)
            if not processed:
                logger.warning(f"Agent '{agent_name}' result invalid.")
                error_for_retry = f"Invalid type {type(res)}"

        if processed:
            processed_results[i] = processed
        else:
            agents_to_retry.append(i)
            processed_results[i] = {"error": error_for_retry, "agent_name": agent_name, "_needs_retry": True}

    retries = config.get("settings", {}).get("retry_limit", 3)
    for attempt in range(retries):
        if not agents_to_retry:
            break

        retry_tasks = []
        retry_map = {}
        await asyncio.sleep(1)

        for original_idx in agents_to_retry:
            agent_name = executed_agent_names[original_idx]
            try:
                agent_instance = agent[agent_name]
                retry_tasks.append(agent_instance.send(payload))
                retry_map[len(retry_tasks)-1] = original_idx
            except Exception as e:
                logger.error(f"Retry error '{agent_name}': {e}", exc_info=True)

        retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)
        next_agents_to_retry = []

        for task_idx, retry_res in enumerate(retry_results):
            original_idx = retry_map[task_idx]
            agent_name = executed_agent_names[original_idx]
            processed = None
            error_for_next_retry = None

            if isinstance(retry_res, Exception):
                error_for_next_retry = str(retry_res)
            else:
                processed = process_agent_result(retry_res, agent_name)
                if not processed:
                    error_for_next_retry = f"Retry {attempt+1} invalid: {type(retry_res)}"

            if processed:
                processed_results[original_idx] = processed
            else:
                next_agents_to_retry.append(original_idx)
                processed_results[original_idx]["error"] = error_for_next_retry

        agents_to_retry = next_agents_to_retry

    final_results = []
    for i, result in enumerate(processed_results):
        agent_name = executed_agent_names[i]
        if result is None:
            final_results.append({"error": "Processing logic error", "agent_name": agent_name})
        elif result.pop("_needs_retry", None):
            final_results.append(result)
        else:
            final_results.append(result)

    return final_results

async def run_pipeline(agent: Any, config: Dict, oracle_sql: str, model_map: Dict[str, str], source_file: str = "") -> Dict:
    candidate_payloads = await run_parallel_conversion(agent, config, oracle_sql, model_map)
    successful_candidates = [
        p.get("postgresql_sql", "")
        for p in candidate_payloads
        if isinstance(p, dict) and "error" not in p and p.get("postgresql_sql")
    ]

    if not successful_candidates:
        failed_info = [p for p in candidate_payloads if isinstance(p, dict) and "error" in p]
        return {"error": f"No valid SQL candidates. Failures: {failed_info}", "postgresql_sql": ""}

    merge_payload = {
        "oracle_sql": oracle_sql,
        "candidates": successful_candidates
    }

    merged_sql = ""
    merged_transformations = []
    processed_merge_result = None
    try:
        merge_agent = agent['merge_and_select']
        merged_result_payload = await merge_agent.send(merge_payload)
        processed_merge_result = process_agent_result(merged_result_payload, "merge_and_select")

        if not processed_merge_result:
            return {"error": "Merge result processing failed", "postgresql_sql": ""}

        merged_sql = processed_merge_result.get("postgresql_sql", "")
        merged_transformations = processed_merge_result.get("transformations", [])

        if not merged_sql:
            return {"error": "Merge agent produced empty SQL", "postgresql_sql": ""}

        if merged_transformations:
            core.knowledge.save_transformations(
                merged_transformations,
                source_file=source_file,
                agent_name="merge_and_select"
            )

    except Exception as e:
        return {"error": f"Merge error: {e}", "postgresql_sql": ""}

    pipeline_payload = {
        "oracle_sql": oracle_sql,
        "postgresql_sql": merged_sql
    }

    final_result_payload = {}
    try:
        pipeline_agent = agent['oracle_to_pg_pipeline']
        final_result_payload_raw = await pipeline_agent.send(pipeline_payload)
        final_result_payload = process_agent_result(final_result_payload_raw, "oracle_to_pg_pipeline")

        if final_result_payload is None:
            final_result_payload = {
                "error": "Pipeline result processing failed",
                "postgresql_sql": merged_sql
            }

        if "postgresql_sql" not in final_result_payload:
            final_result_payload["postgresql_sql"] = merged_sql
        elif not final_result_payload.get("postgresql_sql"):
            final_result_payload["postgresql_sql"] = merged_sql

    except Exception as e:
        return {"error": f"Final pipeline error: {e}", "postgresql_sql": merged_sql}

    return final_result_payload

async def run_single_sql(agent: Any, config: Dict, oracle_sql: str, source_file: str = "") -> Dict:
    model_map = config.get("models", {})
    if not model_map:
        return {"error": "Missing 'models' in config", "postgresql_sql": ""}

    result_payload = await run_pipeline(agent, config, oracle_sql, model_map, source_file)
    return result_payload
