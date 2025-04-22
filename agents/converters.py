# agents/converters.py

"""
🔹 현재 작업: 변환 에이전트 정의
파일: agents/converters.py
목표: converter_1 ~ converter_3 정의
모든 에이전트는 같은 목적의 변환을 수행하며, 모델은 외부에서 설정됨

다음 단계 예고: agents/merge.py 작성 (변환 결과 병합/선택용 에이전트)
"""

from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("SQL Converter Agents")

@fast.agent(name="converter_1", instruction="""
Convert the given Oracle SQL to PostgreSQL.
Return only the converted PostgreSQL SQL.
""")
async def converter_1(payload: dict):
    return payload

@fast.agent(name="converter_2", instruction="""
Convert the given Oracle SQL to PostgreSQL.
Return only the converted PostgreSQL SQL.
""")
async def converter_2(payload: dict):
    return payload

@fast.agent(name="converter_3", instruction="""
Convert the given Oracle SQL to PostgreSQL.
Return only the converted PostgreSQL SQL.
""")
async def converter_3(payload: dict):
    return payload
