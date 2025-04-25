from core.app import fast_agent_instance
from config.loader import load_sqlporter_config

sqlporter_config = load_sqlporter_config()
settings = sqlporter_config.get("settings", {})

@fast_agent_instance.evaluator_optimizer(
    name="oracle_to_pg_pipeline",
    generator="merge_and_select",
    evaluator="sql_evaluator",
    min_rating=settings.get("min_rating", "EXCELLENT"),
    max_refinements=settings.get("max_refinements", 3)
)
async def oracle_to_pg_pipeline(payload: dict):
    return payload
