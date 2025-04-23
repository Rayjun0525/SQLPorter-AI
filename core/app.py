# core/app.py
"""애플리케이션의 중앙 FastAgent 인스턴스를 정의합니다."""

from mcp_agent.core.fastagent import FastAgent

# 애플리케이션 전체에서 사용할 단일 FastAgent 인스턴스
fast_agent_instance = FastAgent("SQLPorter-AI")

# 필요하다면 여기에 추가적인 애플리케이션 레벨 설정이나
# 초기화 로직을 넣을 수도 있습니다.
