# config/loader.py

"""
🔹 현재 작업: 설정 로더 구현
파일: config/loader.py
목표: 루트의 sqlporter.yaml 파일을 로드하고 dict 형태로 반환하는 유틸리티 제공

다음 단계 예고: agents/converters.py 작성 (converter_1~3 정의)
"""

import yaml
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("sqlporter.yaml")

SAMPLE_CONFIG = {
    "models": {
        "converter_1": "generic.gemma3:4b",
        "converter_2": "generic.llama3:2:3b",
        "converter_3": "openai.gpt-4o-mini"
    },
    "api_keys": {
        "openai": "sk-REPLACE-ME",
        "generic": "ollama"
    },
    "endpoints": {
        "openai": "https://api.openai.com/v1",
        "generic": "http://localhost:11434/v1"
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

def generate_sample_yaml(path: Path = DEFAULT_CONFIG_PATH):
    """설정 파일이 없을 경우 샘플 생성"""
    with open(path, "w") as f:
        yaml.dump(SAMPLE_CONFIG, f)
    print(f"✅ 샘플 설정 파일이 {path}에 생성되었습니다.")

def load_sqlporter_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """설정 파일 로드 및 파싱"""
    if not path.exists():
        print("⚠️  설정 파일이 없습니다. 샘플 파일을 생성합니다.")
        generate_sample_yaml(path)
    with open(path, "r") as f:
        return yaml.safe_load(f)
