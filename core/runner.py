import asyncio
import sys
from typing import List, Dict, Any
import logging
import json
import core.knowledge # knowledge 모듈 임포트

logger = logging.getLogger(__name__)

def looks_like_sql(s: str) -> bool:
    """문자열이 SQL 코드처럼 보이는지 간단히 확인합니다."""
    s_upper = s.strip().upper()
    # SQL 주석도 SQL로 간주하도록 수정
    return s_upper.startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'WITH', '--', '/*'))

def process_agent_result(result_data: Any, agent_name: str) -> Dict | None:
    """에이전트 결과를 처리하여 표준 딕셔너리 형식으로 변환하거나 실패 시 None 반환"""
    processed_dict = None # 최종 반환할 딕셔너리

    if isinstance(result_data, dict):
        # 이미 딕셔너리면 일단 사용
        processed_dict = result_data
    elif isinstance(result_data, str):
        # 문자열인 경우 처리
        stripped_res = result_data.strip()
        # 1. JSON 문자열인지 확인 및 파싱 시도
        if stripped_res.startswith('{') and stripped_res.endswith('}'):
            try:
                parsed_json = json.loads(stripped_res)
                if isinstance(parsed_json, dict):
                    processed_dict = parsed_json # JSON 파싱 성공 시 사용
                    logger.info(f"Agent '{agent_name}' returned a valid JSON string. Parsed successfully.")
                else:
                    # 파싱은 성공했으나 결과가 딕셔너리가 아닌 경우 (거의 발생 안 함)
                    logger.warning(f"Agent '{agent_name}' returned a JSON-like string, but parsing resulted in non-dict type. Content: {stripped_res[:200]}...")
            except json.JSONDecodeError:
                # JSON 파싱 실패
                logger.warning(f"Agent '{agent_name}' returned a string starting with '{{' but failed JSON decoding. Content: {stripped_res[:200]}...")
        # 2. JSON이 아니라면, SQL 문자열인지 확인
        elif looks_like_sql(stripped_res):
            logger.warning(f"Agent '{agent_name}' returned a non-JSON string. Assuming it's SQL.")
            # SQL만 있는 딕셔너리 생성
            processed_dict = {"postgresql_sql": stripped_res}
        # 3. JSON도 아니고 SQL도 아닌 문자열
        else:
             logger.warning(f"Agent '{agent_name}' returned an unrecognized string: {stripped_res[:200]}...")
    # 그 외 타입 (None, 숫자 등)
    else:
        logger.warning(f"Agent '{agent_name}' returned unexpected type {type(result_data)}")

    # 처리된 딕셔너리가 있고, 필수 키(postgresql_sql)가 있는지 확인
    if processed_dict is not None and "postgresql_sql" in processed_dict:
        processed_dict["agent_name"] = agent_name # agent_name 추가
        # transformations 키가 없으면 빈 리스트로 초기화
        if "transformations" not in processed_dict:
            processed_dict["transformations"] = []
        return processed_dict
    elif processed_dict is not None: # 딕셔너리는 맞지만 필수 키가 없는 경우
        logger.warning(f"Processed dictionary for agent '{agent_name}' is missing 'postgresql_sql' key.")
        return None # 실패 처리
    else: # 딕셔너리 형태로 처리 실패
        return None

async def run_parallel_conversion(agent: Any, config: Dict, oracle_sql: str, model_map: Dict[str, str]) -> List[Dict]:
    """
    여러 변환 에이전트를 병렬로 실행하고 결과를 반환합니다.
    초기 실행 실패 시, 실패한 에이전트들에 대해 병렬로 재시도합니다.
    문자열 반환 시 SQL 또는 JSON으로 간주하고 처리합니다.
    """
    payload = {"oracle_sql": oracle_sql}
    initial_tasks = []
    executed_agent_names = [] # 실제로 태스크를 생성한 에이전트 이름 목록 (초기 실행 기준)

    # 지식 로드 및 포맷팅
    known_rules = core.knowledge.load_transformations()
    formatted_knowledge = core.knowledge.format_rules_for_prompt(known_rules)
    logger.debug(f"Formatted knowledge for prompt:\n{formatted_knowledge}")

    logger.debug(f"--- Entering run_parallel_conversion ---")
    logger.debug(f"Received model_map: {model_map}")
    logger.debug(f"Using settings: {config.get('settings', {})}")
    logger.debug(f"Preparing initial tasks based on model_map keys: {list(model_map.keys())}")

    # 초기 태스크 준비
    for agent_name in model_map.keys():
        logger.debug(f"Processing agent_name for initial task: '{agent_name}'")
        try:
            agent_instance = agent[agent_name]
            # Payload에 지식 추가
            payload_with_knowledge = payload.copy()
            payload_with_knowledge["known_transformations"] = formatted_knowledge
            initial_tasks.append(agent_instance.send(payload_with_knowledge)) # 수정된 payload 사용
            executed_agent_names.append(agent_name)
            logger.debug(f"Initial task for agent '{agent_name}' appended successfully.")
        except KeyError:
             logger.error(f"KeyError accessing agent '{agent_name}' during initial task prep. Is it defined correctly and loaded?", exc_info=True)
        except Exception as e:
             logger.error(f"Error preparing initial task for agent '{agent_name}': {e}", exc_info=True)

    if not initial_tasks:
        logger.error("실행할 유효한 변환 에이전트가 없습니다.")
        return [{"error": "No valid conversion agents found"}]

    # 1. 초기 병렬 실행
    logger.info(f"Starting initial parallel execution for {len(initial_tasks)} agents...")
    initial_results = await asyncio.gather(*initial_tasks, return_exceptions=True)
    logger.info("Initial parallel execution finished.")

    # 결과 저장 및 재시도 대상 식별
    processed_results: List[Dict | None] = [None] * len(executed_agent_names)
    agents_to_retry: List[int] = [] # 재시도가 필요한 에이전트의 인덱스 저장

    # 초기 결과 처리
    for i, res in enumerate(initial_results):
        agent_name = executed_agent_names[i]
        processed = None # 처리 결과 저장 변수
        error_for_retry = None # 재시도 시 사용할 오류 메시지

        if isinstance(res, Exception):
            # 실행 중 예외 발생
            logger.warning(f"Agent '{agent_name}' failed initial run with exception: {res}. Scheduling for retry.")
            error_for_retry = str(res)
        else:
            # process_agent_result 함수를 사용하여 결과 처리
            processed = process_agent_result(res, agent_name)
            if processed is None: # 처리 실패 시 (잘못된 타입, 파싱 실패 등)
                 logger.warning(f"Agent '{agent_name}' failed initial processing. Scheduling for retry.")
                 # 실패 원인을 좀 더 명확히 하기 위해 원본 타입 기록
                 error_for_retry = f"Initial processing failed for type {type(res)}"

        if processed: # 처리 성공 시
            processed_results[i] = processed
        else: # 처리 실패 시 재시도 목록 추가
            agents_to_retry.append(i)
            processed_results[i] = {"error": f"Initial failure: {error_for_retry}", "agent_name": agent_name, "_needs_retry": True}

    # 2. 병렬 재시도 루프
    retries = config.get("settings", {}).get("retry_limit", 3)
    retry_delay = 1 # 재시도 간격 (초)

    for attempt in range(retries):
        if not agents_to_retry: # 재시도할 에이전트가 없으면 루프 종료
            logger.info("No agents left to retry.")
            break

        logger.info(f"--- Starting Retry Attempt {attempt + 1}/{retries} for {len(agents_to_retry)} agents ---")
        retry_tasks = []
        retry_map = {} # 병렬 재시도 태스크 인덱스 -> 원래 인덱스(i) 매핑

        await asyncio.sleep(retry_delay) # 재시도 전 잠시 대기

        current_retry_agent_names = [executed_agent_names[idx] for idx in agents_to_retry]
        logger.info(f"Retrying agents: {current_retry_agent_names}")

        # 재시도 태스크 준비
        for original_idx in agents_to_retry:
            agent_name = executed_agent_names[original_idx]
            try:
                agent_instance = agent[agent_name]
                task_index = len(retry_tasks)
                # Payload에 지식 추가 (재시도 시)
                payload_with_knowledge = payload.copy()
                payload_with_knowledge["known_transformations"] = formatted_knowledge
                retry_tasks.append(agent_instance.send(payload_with_knowledge)) # 수정된 payload 사용
                retry_map[task_index] = original_idx # 매핑 저장
                logger.debug(f"Retry task added for agent '{agent_name}' (original index {original_idx}).")
            except KeyError:
                logger.error(f"KeyError accessing agent '{agent_name}' during retry prep. Cannot retry.", exc_info=True)
                # 접근 불가 시 재시도 목록에서 제거하고 최종 실패 처리
                if processed_results[original_idx] is not None:
                    processed_results[original_idx]["error"] = f"KeyError accessing agent during retry prep"
                    processed_results[original_idx].pop("_needs_retry", None) # 재시도 필요 없음 표시 제거
            except Exception as e:
                logger.error(f"Error preparing retry task for agent '{agent_name}': {e}", exc_info=True)
                # 준비 중 오류 발생 시도 일단 재시도 목록에 남겨둠 (다음 시도 가능성)

        if not retry_tasks:
            logger.warning("No valid retry tasks could be prepared for this attempt.")
            break # 준비된 재시도 태스크가 없으면 루프 종료

        # 병렬 재시도 실행
        retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)
        logger.info(f"Retry attempt {attempt + 1} finished.")

        next_agents_to_retry = [] # 다음 재시도에 포함될 에이전트 인덱스 목록
        # 재시도 결과 처리
        for task_idx, retry_res in enumerate(retry_results):
            original_idx = retry_map[task_idx]
            agent_name = executed_agent_names[original_idx]
            processed = None # 재시도 처리 결과 저장 변수
            error_for_next_retry = None # 다음 재시도 시 사용할 오류 메시지

            if isinstance(retry_res, Exception):
                 # 재시도 중 예외 발생
                 logger.warning(f"Agent '{agent_name}' failed retry attempt {attempt + 1} with exception: {retry_res}")
                 error_for_next_retry = str(retry_res)
            else:
                # process_agent_result 함수를 사용하여 재시도 결과 처리
                processed = process_agent_result(retry_res, agent_name)
                if processed is None: # 처리 실패 시
                    logger.warning(f"Agent '{agent_name}' failed processing on retry attempt {attempt + 1}.")
                    error_for_next_retry = f"Processing failed on retry {attempt + 1} for type {type(retry_res)}"
                    # 마지막 재시도 실패 시 상세 내용 로깅
                    if attempt == retries - 1:
                         logger.error(f"Agent '{agent_name}' final failure content: {str(retry_res)[:200]}...")

            if processed: # 재시도 처리 성공 시
                logger.info(f"Agent '{agent_name}' succeeded processing on retry attempt {attempt + 1}.")
                processed_results[original_idx] = processed
                # 성공했으므로 next_agents_to_retry에 추가하지 않음
            else: # 재시도 처리 실패 시
                next_agents_to_retry.append(original_idx) # 다음 재시도 목록에 추가
                # 실패 오류 메시지 업데이트 (마지막 재시도 후에 최종 확정됨)
                if processed_results[original_idx] is not None:
                     processed_results[original_idx]["error"] = error_for_next_retry

        agents_to_retry = next_agents_to_retry # 재시도 대상 목록 갱신

    # 3. 최종 결과 정리
    final_results = []
    for i, result in enumerate(processed_results):
        agent_name = executed_agent_names[i]
        if result is None: # 초기화 상태 그대로인 경우 (로직 오류 가능성)
             logger.error(f"Result for agent '{agent_name}' remained None after processing. Adding as error.")
             final_results.append({"error": "Processing logic error, result is None", "agent_name": agent_name})
        elif result.pop("_needs_retry", None): # 재시도 대상이었으나 모든 재시도 실패
            logger.error(f"Agent '{agent_name}' failed after {retries} retries.")
            # 최종 오류 메시지 업데이트
            if "error" not in result: # Should have error from initial failure
                 result["error"] = f"Failed after {retries} retries with unknown final state"
            else:
                 # 오류 메시지가 이미 재시도 실패 정보 포함하도록 수정됨
                 result["error"] = f"Failed after {retries} retries: {result['error']}"
            final_results.append(result)
        else: # 초기 성공 또는 재시도 성공
            final_results.append(result)

    logger.debug(f"--- Exiting run_parallel_conversion ---")
    return final_results

async def run_pipeline(agent: Any, config: Dict, oracle_sql: str, model_map: Dict[str, str]) -> Dict:
    """변환 후보 생성, 병합/선택, 최종 평가/개선 파이프라인을 실행합니다."""
    logger.debug("--- Entering run_pipeline ---")
    # 1. 병렬 변환 실행
    candidate_payloads = await run_parallel_conversion(agent, config, oracle_sql, model_map)
    logger.debug(f"Parallel conversion results: {candidate_payloads}")

    # 2. 성공 후보 추출 (error 키가 없는 dict만 사용)
    successful_candidates = [
        p.get("postgresql_sql", "")
        for p in candidate_payloads
        if isinstance(p, dict) and "error" not in p and p.get("postgresql_sql")
    ]
    logger.debug(f"Successful candidate SQLs for merge: {successful_candidates}")

    if not successful_candidates:
         # 유효한 후보가 없을 경우 처리
         logger.warning("유효한 변환 후보 SQL이 없어 병합/선택을 진행할 수 없습니다.")
         logger.debug("--- Exiting run_pipeline (no successful candidates) ---")
         # 실패한 에이전트들의 오류 메시지를 포함하여 반환
         failed_agents_info = [p for p in candidate_payloads if isinstance(p, dict) and "error" in p]
         error_detail = f"No valid SQL candidates found. Failures: {failed_agents_info}"
         return {"error": error_detail, "postgresql_sql": ""}

    # 3. 병합 단계
    merge_payload = {
        "oracle_sql": oracle_sql,
        "candidates": successful_candidates
    }
    logger.debug(f"Payload for merge_and_select: {merge_payload}")
    merged_sql = ""
    merged_transformations = []
    processed_merge_result = None # 변수 선언
    try:
        logger.debug("Attempting to access 'merge_and_select' agent...")
        merge_agent = agent['merge_and_select']
        logger.debug("'merge_and_select' agent accessed successfully.")

        # merge_and_select 호출
        merged_result_payload = await merge_agent.send(merge_payload)
        logger.debug(f"Result from merge_and_select: {merged_result_payload}") # 원시 결과 로깅

        # 결과 처리
        processed_merge_result = process_agent_result(merged_result_payload, "merge_and_select")
        logger.debug(f"Processed result from merge_and_select: {processed_merge_result}") # 처리된 결과 로깅

        if processed_merge_result is None:
             # 처리 실패 시
             logger.warning(f"병합/선택 에이전트 결과 처리 실패.")
             logger.debug("--- Exiting run_pipeline (merge agent result processing failed) ---")
             return {"error": f"Merge agent result processing failed for type {type(merged_result_payload)}", "postgresql_sql": ""}

        # 성공 시 SQL 및 변환 규칙 추출
        merged_sql = processed_merge_result.get("postgresql_sql", "")
        merged_transformations = processed_merge_result.get("transformations", [])

        if not merged_sql:
            # SQL이 비어있는 경우
            logger.warning("병합/선택 에이전트가 유효한 SQL을 반환하지 못했습니다 (처리 후).")
            logger.debug("--- Exiting run_pipeline (merge agent failed to produce SQL after processing) ---")
            return {"error": "Merge agent failed to produce SQL after processing", "postgresql_sql": ""}

        # --- 지식 저장 로직 (병합 단계 직후) ---
        if merged_transformations:
             logger.info(f"Saving {len(merged_transformations)} transformations found during merge step.")
             core.knowledge.save_transformations(merged_transformations) # 저장 함수 호출
        else:
             # transformations가 비어있으면 로그 남기기
             logger.info("No transformations found or reported by merge_and_select agent.")
        # --- 저장 로직 끝 ---

    except KeyError:
        # 에이전트 접근 실패
        logger.error("병합/선택 에이전트('merge_and_select') 접근 중 KeyError 발생.", exc_info=True)
        logger.debug("--- Exiting run_pipeline (error during merge/select access) ---")
        return {"error": "KeyError accessing merge agent: 'merge_and_select'", "postgresql_sql": ""}
    except Exception as e:
        # 그 외 실행 오류
        logger.error(f"병합/선택 에이전트 실행 중 오류 발생: {e}", exc_info=True)
        logger.debug("--- Exiting run_pipeline (error during merge/select execution) ---")
        return {"error": f"Error during merge/select: {e}", "postgresql_sql": ""}

    # 4. 최종 파이프라인 단계
    pipeline_payload = {
        "oracle_sql": oracle_sql,
        "postgresql_sql": merged_sql # 병합된 SQL 전달
    }
    logger.debug(f"Payload for oracle_to_pg_pipeline: {pipeline_payload}")
    final_result_payload = {} # 최종 결과 저장 변수
    try:
         logger.debug("Attempting to access 'oracle_to_pg_pipeline' agent...")
         pipeline_agent = agent['oracle_to_pg_pipeline']
         logger.debug("'oracle_to_pg_pipeline' agent accessed successfully.")

         # 파이프라인 에이전트 호출
         final_result_payload_raw = await pipeline_agent.send(pipeline_payload)
         logger.debug(f"RAW response from oracle_to_pg_pipeline: {final_result_payload_raw} (Type: {type(final_result_payload_raw)})") # 원시 결과 로깅

         # 결과 처리
         final_result_payload = process_agent_result(final_result_payload_raw, "oracle_to_pg_pipeline")

         if final_result_payload is None:
             # 처리 실패 시 병합된 SQL 사용
             logger.warning(f"최종 파이프라인 에이전트 결과 처리 실패. 병합된 SQL 사용.")
             final_result_payload = {"error": f"Pipeline agent result processing failed for type {type(final_result_payload_raw)}", "postgresql_sql": merged_sql}
         # else:
             # 최종 단계에서는 변환 규칙 저장 로직 제거 (병합 단계에서만 저장)

         # 최종 SQL 키 확인 및 처리
         if "postgresql_sql" not in final_result_payload:
             logger.warning("Final pipeline payload does not contain 'postgresql_sql' key after processing. Using merged SQL.")
             final_result_payload["postgresql_sql"] = merged_sql
         elif not final_result_payload.get("postgresql_sql"): # 키는 있지만 값이 비어있는 경우
             logger.warning("Final pipeline payload has an empty 'postgresql_sql' value after processing. Using merged SQL.")
             final_result_payload["postgresql_sql"] = merged_sql

         logger.debug("--- Exiting run_pipeline (success) ---")
         return final_result_payload

    except KeyError:
        # 에이전트 접근 실패
        logger.error("최종 파이프라인 에이전트('oracle_to_pg_pipeline') 접근 중 KeyError 발생.", exc_info=True)
        logger.debug("--- Exiting run_pipeline (error during pipeline access) ---")
        return {"error": "KeyError accessing pipeline agent: 'oracle_to_pg_pipeline'", "postgresql_sql": merged_sql} # 병합된 SQL이라도 반환
    except Exception as e:
        # 그 외 실행 오류
        logger.error(f"최종 파이프라인 에이전트 실행 중 오류 발생: {e}", exc_info=True)
        logger.debug("--- Exiting run_pipeline (error during final pipeline execution) ---")
        return {"error": f"Error during final pipeline: {e}", "postgresql_sql": merged_sql} # 병합된 SQL이라도 반환

async def run_single_sql(agent: Any, config: Dict, oracle_sql: str) -> str:
    """단일 Oracle SQL에 대해 전체 변환 파이프라인을 실행하고 최종 SQL 문자열을 반환합니다."""
    logger.debug("--- Entering run_single_sql ---")
    # 설정에서 모델 맵 가져오기
    model_map = config.get("models", {})
    if not model_map:
        logger.error("설정 파일에 'models' 정보가 없습니다. 변환을 진행할 수 없습니다.")
        logger.debug("--- Exiting run_single_sql (no models in config) ---")
        return "" # 빈 문자열 반환
    logger.debug(f"Using model_map: {model_map}")

    # 파이프라인 실행
    result_payload = await run_pipeline(agent, config, oracle_sql, model_map)
    logger.debug(f"Result payload from run_pipeline: {result_payload}")

    # 최종 SQL 추출
    final_sql = result_payload.get("postgresql_sql", "")

    # 오류 로깅
    if "error" in result_payload:
        if not final_sql:
            logger.info(f"파이프라인 실행 중 오류 발생: {result_payload['error']}. 빈 SQL 반환.")
        else:
            # 최종 SQL은 있지만 오류 메시지도 있는 경우
            logger.warning(f"파이프라인 실행 중 오류 발생: {result_payload['error']}. 중간 결과 SQL 반환.")

    # 반환할 SQL 로깅 (길이 제한)
    log_sql = (final_sql[:100] + '...') if len(final_sql) > 100 else final_sql
    logger.debug(f"Final SQL to return (truncated): {log_sql}")
    logger.debug("--- Exiting run_single_sql ---")
    return final_sql
