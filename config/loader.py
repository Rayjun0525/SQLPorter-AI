import yaml
from pathlib import Path
import sys

DEFAULT_CONFIG_PATH = Path("fastagent.config.yaml")

SAMPLE_CONFIG = {
    "logger": {
        "level": "INFO",
        "type": "both",
        "path": "./logs/sqlporter.log",
        "progress_display": True,
        "show_chat": True,
        "show_tools": True,
        "truncate_tools": True
    },
    "sqlporter": {
        "models": {
            "converter_1": "generic.gemma3:4b",
            "converter_2": "generic.llama3.2:3b",
            "converter_3": "openai.gpt-4o-mini"
        },
        "instructions": {
            "converter_1": "",
            "converter_2": (
                "Convert the Oracle SQL to PostgreSQL using Llama3-specific syntax rules.\n"
                "Respond ONLY with JSON as described in the default instruction."
            ),
            "converter_3": ""
        },
        "paths": {
            "input_dir": "./ASIS",
            "output_dir": "./TOBE",
            "report_dir": "./reports"
        },
        "settings": {
            "max_refinements": 3,
            "min_rating": "EXCELLENT",
            "retry_limit": 3,
            "comment_prefix": "--"
        }
    }
}

def generate_sample_yaml(path: Path = DEFAULT_CONFIG_PATH):
    """Generate a full sample config file if one does not exist."""
    try:
        with open(path, "w", encoding='utf-8') as f:
            yaml.dump(SAMPLE_CONFIG, f, allow_unicode=True, sort_keys=False)
        print(f"Sample config generated at {path}. Please review and customize it.")
    except IOError as e:
        print(f"Error creating sample config: {e}", file=sys.stderr)
        sys.exit(1)

def load_sqlporter_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """Load the configuration YAML file and return the sqlporter section."""
    if not path.exists():
        print(f"Config file ({path}) not found. Creating a sample...")
        generate_sample_yaml(path)

    try:
        with open(path, "r", encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if config is None or "sqlporter" not in config:
                print(f"Invalid or missing 'sqlporter' section in {path}.", file=sys.stderr)
                sys.exit(1)

            sqlporter_config = config["sqlporter"]
            
            # 경로 검증
            paths = sqlporter_config.get("paths", {})
            for dir_name, dir_path in paths.items():
                if not dir_path:
                    print(f"Warning: Empty path for {dir_name}")
                    continue
                
                path_obj = Path(dir_path)
                if not path_obj.exists():
                    print(f"Warning: {dir_name} path does not exist: {dir_path}")
                    # 경로가 없으면 자동 생성
                    path_obj.mkdir(parents=True, exist_ok=True)
                    print(f"Created directory: {dir_path}")

            return sqlporter_config
    except yaml.YAMLError as e:
        print(f"YAML parsing error in config file ({path}): {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading config file ({path}): {e}", file=sys.stderr)
        sys.exit(1)
