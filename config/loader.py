import yaml
from pathlib import Path
import sys

DEFAULT_CONFIG_PATH = Path("fastagent.config.yaml")

SAMPLE_CONFIG = {
    "sqlporter": {
        "models": {
            "converter_1": "generic.gemma3:4b",
            "converter_2": "generic.llama3:2:3b",
            "converter_3": "openai.gpt-4o-mini"
        },
        "instructions": {
            "converter_1": "",
            "converter_2": "Convert the Oracle SQL to PostgreSQL using Llama3-specific syntax rules.",
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
    """Generate a sample config file if one does not exist."""
    try:
        with open(path, "w", encoding='utf-8') as f:
            yaml.dump(SAMPLE_CONFIG, f, allow_unicode=True, sort_keys=False)
        print(f"Sample config generated at {path}. Please review and customize it.")
    except IOError as e:
        print(f"Error creating sample config: {e}", file=sys.stderr)
        sys.exit(1)

def load_sqlporter_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """Load the configuration YAML file."""
    if not path.exists():
        print(f"Config file ({path}) not found. Creating a sample...")
        generate_sample_yaml(path)

    try:
        with open(path, "r", encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if config is None or "sqlporter" not in config:
                print(f"Invalid or missing 'sqlporter' section in {path}.", file=sys.stderr)
                sys.exit(1)
            return config["sqlporter"]
    except yaml.YAMLError as e:
        print(f"YAML parsing error in config file ({path}): {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading config file ({path}): {e}", file=sys.stderr)
        sys.exit(1)
