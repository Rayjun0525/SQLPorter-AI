from core.app import fast_agent_instance

@fast_agent_instance.evaluator_optimizer(
    name="oracle_to_pg_pipeline",
    generator="merge_and_select",
    evaluator="sql_evaluator",
    min_rating="EXCELLENT",
    max_refinements=3
)
async def oracle_to_pg_pipeline(payload: dict):
    return payload
