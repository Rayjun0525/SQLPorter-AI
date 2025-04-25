import argparse
import asyncio
import logging
import sys
from pathlib import Path

from config.loader import load_sqlporter_config
from config.logging_config import setup_logging
from core.file_io import (
    get_sql_files,
    read_sql_file,
    write_sql_with_comment,
    write_report,
    write_html_report
)
from core.runner import run_single_sql

from core.app import fast_agent_instance

import agents.converters
import agents.merge
import agents.evaluator
import agents.pipeline

__version__ = "1.0.0"

def resource_path(relative_path: str) -> Path:
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).parent
    return base_path / relative_path

def main():
    parser = argparse.ArgumentParser(description="SQLPorter-AI")
    parser.add_argument("--config", type=Path, default=Path("fastagent.config.yaml"), help="Path to config file")
    parser.add_argument("--secret", type=Path, default=Path("fastagent.secrets.yaml"), help="Path to secret file")
    parser.add_argument("--version", action="store_true", help="Print version and exit")

    args = parser.parse_args()

    if args.version:
        print(f"SQLPorter-AI version {__version__}")
        return

    config_path = resource_path(args.config)
    config = load_sqlporter_config(config_path)
    setup_logging(config.get("logger", {}))

    paths = config.get("paths", {})
    input_dir = resource_path(paths.get("input_dir", "./ASIS"))
    output_dir = resource_path(paths.get("output_dir", "./TOBE"))
    report_dir = resource_path(paths.get("report_dir", "./reports"))
    prefix = config.get("settings", {}).get("comment_prefix", "--")

    summary = {}

    async def run_agents():
        async with fast_agent_instance.run() as agent:
            sql_files = get_sql_files(input_dir)
            if not sql_files:
                logging.warning(f"No SQL files found in '{input_dir}'.")
                return

            logging.info(f"Processing {len(sql_files)} SQL files...")

            for sql_path in sql_files:
                logging.info(f"Processing file: {sql_path.name}")
                try:
                    oracle_sql = read_sql_file(sql_path)
                    result_payload = await run_single_sql(agent, config, oracle_sql, sql_path.name)

                    final_sql = result_payload.get("postgresql_sql", "")
                    comment = f"Converted from: {sql_path.name}"
                    write_sql_with_comment(output_dir, input_dir, sql_path, final_sql, comment, prefix)

                    summary[sql_path.name] = {
                        "status": "success" if final_sql else "incomplete",
                        "error": result_payload.get("error", ""),
                        "rating": result_payload.get("RATING", ""),
                        "feedback": result_payload.get("FEEDBACK", "")
                    }

                    logging.info(f"Finished: {sql_path.name}")

                except FileNotFoundError:
                    logging.error(f"File not found: {sql_path.name}")
                    summary[sql_path.name] = {"status": "error", "message": "File not found"}
                except IOError as e:
                    logging.error(f"I/O error while processing {sql_path.name}: {e}")
                    summary[sql_path.name] = {"status": "error", "message": f"I/O Error: {e}"}
                except Exception as e:
                    logging.exception(f"Unexpected error while processing {sql_path.name}: {e}")
                    summary[sql_path.name] = {"status": "error", "message": str(e)}

    try:
        asyncio.run(run_agents())
    except Exception as e:
        logging.exception(f"Fatal error during FastAgent execution: {e}")
        return

    try:
        report_file = report_dir / "result_summary.json"
        write_report(report_file, summary)
        write_html_report(report_file, summary)
        logging.info(f"Conversion complete. Report generated: {report_file}")
    except Exception as e:
        logging.exception(f"Unexpected error while writing report: {e}")

if __name__ == "__main__":
    main()