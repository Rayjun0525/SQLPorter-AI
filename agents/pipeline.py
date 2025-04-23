# agents/pipeline.py
"""SQL 변환 및 평가 파이프라인(oracle_to_pg_pipeline)을 정의합니다."""

from core.app import fast_agent_instance # 중앙 FastAgent 인스턴스 임포트
# from mcp_agent.core.fastagent import FastAgent # 로컬 임포트 제거

# fast = FastAgent("SQL Evaluation Pipeline") # 로컬 인스턴스 생성 제거

@fast_agent_instance.evaluator_optimizer(
    name="oracle_to_pg_pipeline",
    generator="merge_and_select", # 병합/선택 에이전트 사용
    evaluator="sql_evaluator",     # 평가 에이전트 사용
    min_rating="EXCELLENT",        # 목표 평가 등급
    max_refinements=3              # 최대 개선 시도 횟수
)
async def oracle_to_pg_pipeline(payload: dict):
    # fast-agent 프레임워크가 파이프라인 실행 및 페이로드 처리를 담당
    return payload
