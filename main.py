import asyncio
import logging
from pathlib import Path
import typer

from config.loader import load_sqlporter_config
from config.logging_config import setup_logging
from core.runner import run_single_sql
from core.file_io import get_sql_files, read_sql_file, write_sql_with_comment, write_report, write_html_report
from core.app import fast_agent_instance

import agents.converters
import agents.merge
import agents.evaluator
import agents.pipeline

app = typer.Typer()
__version__ = "1.0.0"

@app.command()
def run(
    config_path: Path = Path("fastagent.config.yaml"),
    secret_path: Path = Path("fastagent.secrets.yaml")
):
    try:
        config = load_sqlporter_config(config_path)
    except SystemExit:
        logging.error("Failed to load configuration file. Exiting.")
        return

    setup_logging(config.get("logger", {}))

    paths = config.get("paths", {})
    input_dir = Path(paths.get("input_dir", "./ASIS"))
    output_dir = Path(paths.get("output_dir", "./TOBE"))
    report_dir = Path(paths.get("report_dir", "./reports"))
    prefix = config.get("settings", {}).get("comment_prefix", "--")

    summary = {}
    logging.info("Starting SQL conversion process...")

    try:
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

        asyncio.run(run_agents())

    except Exception as e:
        logging.exception(f"Fatal error during FastAgent execution: {e}")
        return

    try:
        report_file = report_dir / "result_summary.json"
        write_report(report_file, summary)
        write_html_report(report_file, summary)
        logging.info(f"Conversion complete. Report generated: {report_file}")
    except IOError as e:
        logging.error(f"Failed to write report file: {e}")
    except Exception as e:
        logging.exception(f"Unexpected error while writing report: {e}")

@app.command()
def version():
    """Show the current version of SQLPorter-AI."""
    typer.echo(f"SQLPorter-AI version {__version__}")

if __name__ == "__main__":
    app()
