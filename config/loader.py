# config/loader.py
"""설정 파일(sqlporter.yaml) 로드 유틸리티"""

import yaml
from pathlib import Path
import sys # sys 모듈 임포트 추가

DEFAULT_CONFIG_PATH = Path("sqlporter.yaml")

# 샘플 설정 내용 (기본값으로 사용)
SAMPLE_CONFIG = {
    "models": {
        "converter_1": "generic.gemma3:4b",
        "converter_2": "generic.llama3:2:3b",
        "converter_3": "openai.gpt-4o-mini"
    },
    "api_keys": {
        "openai": "sk-REPLACE-ME",
        "generic": "ollama" # Ollama 사용 시 API 키 불필요
    },
    "endpoints": {
        "openai": "https://api.openai.com/v1",
        "generic": "http://localhost:11434/v1" # 로컬 Ollama 엔드포인트
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
    """설정 파일이 없을 경우 샘플 설정 파일을 생성합니다."""
    try:
        with open(path, "w", encoding='utf-8') as f: # encoding 추가
            yaml.dump(SAMPLE_CONFIG, f, allow_unicode=True, sort_keys=False) # 옵션 추가
        print(f"✅ 샘플 설정 파일이 {path}에 생성되었습니다. API 키 등을 수정해주세요.")
    except IOError as e:
        print(f"❌ 샘플 설정 파일 생성 중 오류 발생: {e}", file=sys.stderr)
        sys.exit(1) # 오류 발생 시 종료

def load_sqlporter_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """지정된 경로의 YAML 설정 파일을 로드하고 파싱합니다."""
    if not path.exists():
        print(f"⚠️ 설정 파일({path})이 없습니다. 샘플 파일을 생성합니다.")
        generate_sample_yaml(path)
        # 샘플 생성 후 사용자에게 수정을 유도하고 종료할 수도 있음
        # print("ℹ️ 생성된 샘플 파일(sqlporter.yaml)의 내용을 확인하고 API 키 등을 설정한 후 다시 실행해주세요.")
        # sys.exit(0)

    try:
        with open(path, "r", encoding='utf-8') as f: # encoding 추가
            config = yaml.safe_load(f)
            if config is None: # 파일은 있지만 내용이 비어있는 경우
                 print(f"❌ 설정 파일({path})이 비어있습니다. 내용을 확인해주세요.", file=sys.stderr)
                 sys.exit(1)
            return config
    except FileNotFoundError:
        # 이 경우는 위 path.exists()에서 처리되지만, 만약을 대비
        print(f"❌ 설정 파일({path})을 찾을 수 없습니다.", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ 설정 파일({path}) 파싱 중 오류 발생: {e}", file=sys.stderr)
        print("ℹ️ YAML 형식이 올바른지 확인해주세요.")
        sys.exit(1)
    except IOError as e:
        print(f"❌ 설정 파일({path}) 읽기 중 오류 발생: {e}", file=sys.stderr)
        sys.exit(1)

