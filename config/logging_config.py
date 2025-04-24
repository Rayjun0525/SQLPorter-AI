import logging
from pathlib import Path

def setup_logging(logger_config: dict):
    level_name = logger_config.get("level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_type = logger_config.get("type", "console")
    log_path = logger_config.get("path", "./logs/sqlporter.log")

    handlers = []
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    if log_type in ("console", "both"):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)

    if log_type in ("file", "both"):
        log_file = Path(log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers, force=True)
    logging.info(f"Logging initialized. Level={level_name}, Type={log_type}")
