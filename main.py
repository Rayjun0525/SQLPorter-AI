# main.py

import asyncio
import logging # logging 모듈 추가
from pathlib import Path
from config.loader import load_sqlporter_config
from core.runner import run_single_sql
from core.file_io import get_sql_files, read_sql_file, write_sql_with_comment, write_report
from core.app import fast_agent_instance # 중앙 FastAgent 인스턴스 임포트

# 에이전트 정의 모듈 임포트 (등록을 위해 필요)
import agents.converters
import agents.merge
import agents.evaluator
import agents.pipeline

# 기본 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    # 설정 로드
    try:
        config = load_sqlporter_config()
    except SystemExit: # load_sqlporter_config에서 오류 시 sys.exit() 호출하므로 처리
        logging.error("설정 파일 로드 실패. 프로그램을 종료합니다.")
        return # main 함수 종료

    input_dir = Path(config["paths"]["input_dir"])
    output_dir = Path(config["paths"]["output_dir"])
    report_dir = Path(config["paths"]["report_dir"])
    prefix = config["settings"].get("comment_prefix", "--")

    # 출력 및 리포트 디렉토리 생성 (file_io에서 처리하므로 주석 처리 또는 제거 가능)
    # output_dir.mkdir(exist_ok=True)
    # report_dir.mkdir(exist_ok=True)
    # file_io의 write 함수들이 부모 디렉토리를 생성해주므로 여기서 미리 만들 필요는 없습니다.

    summary = {} # 결과 요약 저장용

    logging.info("SQL 변환 작업을 시작합니다...")

    # 중앙 FastAgent 인스턴스를 사용하여 에이전트 실행
    try:
        async with fast_agent_instance.run() as agent:
            sql_files = get_sql_files(input_dir)
            if not sql_files:
                logging.warning(f"입력 디렉토리 '{input_dir}'에 SQL 파일이 없습니다.")
                return

            logging.info(f"총 {len(sql_files)}개의 SQL 파일을 처리합니다.")

            for sql_path in sql_files:
                logging.info(f"파일 처리 시작: {sql_path.name}")
                try:
                    oracle_sql = read_sql_file(sql_path)
                    # run_single_sql 호출 시 agent 객체 전달
                    result_sql = await run_single_sql(agent, config, oracle_sql)

                    # 결과 파일 작성
                    comment = f"Converted from: {sql_path.name}"
                    out_path = output_dir / sql_path.name
                    write_sql_with_comment(out_path, result_sql, comment, prefix)

                    summary[sql_path.name] = {"status": "success"}
                    logging.info(f"파일 처리 완료: {sql_path.name} -> {out_path.name}")

                except FileNotFoundError: # read_sql_file에서 sys.exit 대신 예외 발생 시
                    logging.error(f"파일을 찾을 수 없어 건너<0xEB><0><0x8A><0xB4>니다: {sql_path.name}")
                    summary[sql_path.name] = {"status": "error", "message": "File not found"}
                except IOError as e: # read/write 에서 sys.exit 대신 예외 발생 시
                     logging.error(f"파일 처리 중 입출력 오류 발생 ({sql_path.name}): {e}")
                     summary[sql_path.name] = {"status": "error", "message": f"IO Error: {e}"}
                except Exception as e:
                    logging.exception(f"파일 처리 중 예상치 못한 오류 발생 ({sql_path.name}): {e}") # 스택 트레이스 포함 로깅
                    summary[sql_path.name] = {"status": "error", "message": str(e)}

    except Exception as e:
        logging.exception(f"FastAgent 실행 중 오류 발생: {e}")
        # 필요하다면 여기에서 추가적인 정리 작업 수행
        return # 에이전트 실행 실패 시 리포트 작성 전 종료

    # 최종 리포트 작성
    try:
        report_file = report_dir / "result_summary.json"
        write_report(report_file, summary)
        logging.info(f"✅ 변환 완료. 리포트 생성됨: {report_file}")
    except IOError as e: # write_report에서 sys.exit 대신 예외 발생 시
        logging.error(f"리포트 파일 작성 중 오류 발생: {e}")
    except Exception as e:
        logging.exception(f"리포트 작성 중 예상치 못한 오류 발생: {e}")


if __name__ == "__main__":
    asyncio.run(main())

