# core/knowledge.py (신규 생성)

import json
import os
from pathlib import Path
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# 지식 베이스 파일 경로 설정 (프로젝트 루트 기준)
DEFAULT_KNOWLEDGE_DIR = Path("./knowledge")
DEFAULT_KNOWLEDGE_FILE = DEFAULT_KNOWLEDGE_DIR / "transformations.json"

def load_transformations(file_path: Path = DEFAULT_KNOWLEDGE_FILE) -> Dict[str, Any]:
    """지식 베이스 파일(JSON)을 로드하여 딕셔너리로 반환합니다."""
    if not file_path.exists():
        logger.info(f"Knowledge base file not found at {file_path}. Returning empty dictionary.")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            knowledge = json.load(f)
            if not isinstance(knowledge, dict):
                logger.warning(f"Knowledge base file {file_path} does not contain a valid dictionary. Returning empty.")
                return {}
            logger.info(f"Successfully loaded knowledge base from {file_path}")
            return knowledge
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error loading knowledge base from {file_path}: {e}", exc_info=True)
        return {}

def save_transformations(new_rules: List[Dict[str, str]], file_path: Path = DEFAULT_KNOWLEDGE_FILE):
    """새로운 변환 규칙을 기존 지식 베이스(JSON)에 병합하여 저장합니다."""
    if not new_rules:
        return # 저장할 새 규칙이 없으면 종료

    # 디렉토리 없으면 생성
    DEFAULT_KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    current_knowledge = load_transformations(file_path)
    updated_count = 0
    added_count = 0

    for rule in new_rules:
        # 간단한 규칙 (from -> to)만 우선 처리 가정
        # 더 복잡한 규칙(예: 함수 시그니처 변경)은 다른 키 구조나 처리 방식 필요
        from_pattern = rule.get("from")
        to_pattern = rule.get("to")
        context = rule.get("context", "unknown") # 컨텍스트 정보 활용 (선택 사항)

        if from_pattern and to_pattern:
            # 간단한 키-값 저장 (Oracle 패턴 -> PostgreSQL 패턴)
            # 이미 존재하는 규칙이면 업데이트, 없으면 추가
            if from_pattern in current_knowledge and current_knowledge[from_pattern] != to_pattern:
                logger.debug(f"Updating transformation rule: '{from_pattern}' -> '{to_pattern}' (was '{current_knowledge[from_pattern]}')")
                current_knowledge[from_pattern] = to_pattern
                updated_count += 1
            elif from_pattern not in current_knowledge:
                logger.debug(f"Adding new transformation rule: '{from_pattern}' -> '{to_pattern}'")
                current_knowledge[from_pattern] = to_pattern
                added_count += 1

    if updated_count > 0 or added_count > 0:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(current_knowledge, f, indent=2, ensure_ascii=False)
            logger.info(f"Knowledge base updated at {file_path}. Added: {added_count}, Updated: {updated_count}")
        except IOError as e:
            logger.error(f"Error saving knowledge base to {file_path}: {e}", exc_info=True)
    else:
        logger.info("No new or updated transformations to save.")

def format_rules_for_prompt(knowledge: Dict[str, Any]) -> str:
    """지식 베이스 딕셔너리를 LLM 프롬프트에 넣기 좋은 문자열로 변환합니다."""
    if not knowledge:
        return "No known transformation rules available."

    rule_strings = [f"- {oracle_pattern} -> {pg_pattern}" for oracle_pattern, pg_pattern in knowledge.items()]
    return "Here are some known transformation rules:\n" + "\n".join(rule_strings)
