import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("OracleToPostgresAgent")

@fast.agent(
    name="port_oracle_to_postgres",
instruction="""
You are a strict validator.

Given:
1. The original Oracle SQL.
2. The PostgreSQL SQL that was translated.

Evaluate:
- Is the converted PostgreSQL query accurate, equivalent, and executable?
- Are all Oracle-specific elements correctly ported?
- Does any semantic or syntax issue remain?

Respond with the following JSON object **ONLY**, no markdown, no explanation, no text before or after:

{"result": 0 or 1, "feedback": "If result is 1, explain what must be fixed. If result is 0, leave empty."}
"""
)
async def port_oracle_to_postgres(oracle_sql):
    async with fast.run() as agent:
        return await agent(oracle_sql)

@fast.agent(
    name="verify_sql_conversion_strict",
    instruction="""
You are a strict validator.

Given:
1. The original Oracle SQL.
2. The PostgreSQL SQL that was translated.

Evaluate:
- Is the converted PostgreSQL query accurate, equivalent, and executable?
- Are all Oracle-specific elements correctly ported?
- Does any semantic or syntax issue remain?

Respond ONLY in the following JSON format:

{
  "result": 0 or 1,
  "feedback": "If result is 1, explain what must be fixed. If result is 0, leave empty."
}
"""
)
async def verify_sql_conversion_strict(payload: dict):
    async with fast.run() as agent:
        return await agent(payload)

def load_sql_from_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def write_output_sql(sql: str):
    with open("output.sql", "w", encoding="utf-8") as f:
        f.write("-- ✅ PostgreSQL SQL Converted from Oracle\n")
        f.write(sql.strip() + "\n")

async def run_pipeline(oracle_sql: str, max_attempts: int = 10):
    async with fast.run() as agent:
        current_sql = oracle_sql

        for attempt in range(1, max_attempts + 1):
            print(f"🔄 포팅 시도 {attempt} ...")
            converted_sql = await agent.port_oracle_to_postgres(current_sql)

            verification_result_raw = await agent.verify_sql_conversion_strict({
                "oracle_sql": oracle_sql,
                "postgresql_sql": converted_sql
            })

            try:
                verification_result = eval(verification_result_raw) if isinstance(verification_result_raw, str) else verification_result_raw
                result = verification_result.get("result")
                feedback = verification_result.get("feedback", "").strip()
            except Exception:
                print("❌ 검수 JSON 파싱 실패. 응답 포맷 확인 필요.")
                break

            if result == 0:
                print("✅ 검수 통과. 변환 완료.")
                write_output_sql(converted_sql)
                return
            else:
                print(f"❌ 검수 실패: {feedback}")
                current_sql += f"\n-- 검수 피드백 반영: {feedback}"

        print("🚫 최대 시도 횟수 초과. 변환 실패.")

if __name__ == "__main__":
    oracle_sql = load_sql_from_file("input.sql")
    asyncio.run(run_pipeline(oracle_sql))
