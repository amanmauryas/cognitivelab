"""Generic JSON questionnaire rendering and loading engine.

Provides reusable utilities for discovering, loading, and validating
diagnostic scales defined as JSON schemas under diagnostics/definitions/.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFINITIONS_DIR = Path(__file__).resolve().parent / "definitions"


def list_available_scales() -> List[Dict[str, Any]]:
    """Scan the definitions directory and return metadata for all valid scales."""
    scales = []
    if not DEFINITIONS_DIR.exists():
        return scales

    for file_path in sorted(DEFINITIONS_DIR.glob("*.json")):
        definition = load_scale_definition(file_path.stem)
        if definition:
            scales.append({
                "id": definition.get("id", file_path.stem),
                "name": definition.get("name", file_path.stem.upper()),
                "title": definition.get("title", ""),
                "category": definition.get("category", "General"),
                "description": definition.get("description", ""),
                "question_count": len(definition.get("questions", [])),
                "status": "available",
            })
    return scales


def load_scale_definition(scale_id: str) -> Optional[Dict[str, Any]]:
    """Load and parse a scale JSON definition file by its identifier.

    Args:
        scale_id: Base filename without extension (e.g. 'phq9').

    Returns:
        Parsed dictionary if valid, or None if the file does not exist or is invalid JSON.
    """
    file_path = DEFINITIONS_DIR / f"{scale_id}.json"
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            definition = json.load(f)

        is_valid, _ = validate_scale_definition(definition)
        return definition if is_valid else None
    except (json.JSONDecodeError, OSError):
        return None


def validate_scale_definition(definition: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify that a scale definition adheres to required structure.

    Required top-level keys: 'id', 'title', 'questions', 'response_scale', 'scoring'.
    """
    if not isinstance(definition, dict):
        return False, "Definition must be a JSON object"

    required_keys = ["id", "title", "questions", "response_scale", "scoring"]
    for key in required_keys:
        if key not in definition:
            return False, f"Missing required definition key: '{key}'"

    if not isinstance(definition["questions"], list) or len(definition["questions"]) == 0:
        return False, "Definition must include at least one question"

    if not isinstance(definition["response_scale"], list) or len(definition["response_scale"]) == 0:
        return False, "Definition must include a non-empty response_scale"

    return True, "Valid"


def validate_responses(definition: Dict[str, Any], responses: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate submitted responses against the scale's questions and allowed values.

    Args:
        definition: The loaded scale definition dictionary.
        responses: Mapping of question IDs to selected values.

    Returns:
        (is_valid, error_message)
    """
    valid_values = {item["value"] for item in definition.get("response_scale", [])}
    questions = definition.get("questions", [])

    for q in questions:
        q_id = q.get("id")
        if q_id not in responses:
            return False, f"Missing response for question #{q.get('number', q_id)}: {q.get('text', '')}"

        val = responses[q_id]
        try:
            val_num = int(val)
        except (ValueError, TypeError):
            return False, f"Invalid value for question {q_id}: {val}"

        if val_num not in valid_values:
            return False, f"Value {val_num} for question {q_id} is not within the allowed response scale."

    return True, None
