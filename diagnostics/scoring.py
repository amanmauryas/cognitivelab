"""Diagnostic scale scoring engine.

Provides generic scoring, cut-off interpretation, and response mapping
based on declarative scoring rules configured in questionnaire JSON definitions.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def score_assessment(definition: Dict[str, Any], responses: Dict[str, Any]) -> Dict[str, Any]:
    """Score a questionnaire assessment based on its JSON definition.

    Args:
        definition: Parsed questionnaire JSON dictionary.
        responses: Mapping of question IDs to response integer values.

    Returns:
        Structured result dictionary containing total score, max possible score,
        percentage, interpretation label, item breakdown, and educational disclaimer.
    """
    scoring_cfg = definition.get("scoring", {})
    method = scoring_cfg.get("method", "sum")
    response_scale = {item["value"]: item["label"] for item in definition.get("response_scale", [])}
    questions = definition.get("questions", [])

    total_score = 0
    item_breakdown = []

    for q in questions:
        q_id = q.get("id")
        raw_val = responses.get(q_id, 0)
        try:
            val = int(raw_val)
        except (ValueError, TypeError):
            val = 0

        total_score += val
        item_breakdown.append({
            "number": q.get("number"),
            "question_id": q_id,
            "question_text": q.get("text"),
            "value": val,
            "label": response_scale.get(val, str(val)),
        })

    max_score = scoring_cfg.get("max_score", len(questions) * 3)
    min_score = scoring_cfg.get("min_score", 0)

    # Interpretation bands
    interpretation_bands: List[Dict[str, Any]] = scoring_cfg.get("interpretation", [])
    interpretation_label = "Unclassified"

    for band in interpretation_bands:
        b_min = band.get("min", min_score)
        b_max = band.get("max", max_score)
        if b_min <= total_score <= b_max:
            interpretation_label = band.get("label", "Unclassified")
            break

    score_percentage = (total_score / max_score * 100.0) if max_score > 0 else 0.0

    return {
        "scale_id": definition.get("id"),
        "scale_title": definition.get("title", definition.get("name")),
        "category": definition.get("category"),
        "scoring_method": method,
        "total_score": total_score,
        "min_score": min_score,
        "max_score": max_score,
        "percentage": round(score_percentage, 1),
        "interpretation": interpretation_label,
        "item_breakdown": item_breakdown,
        "disclaimer": (
            "Educational and behavioral research screening only. "
            "This automated score does not constitute a clinical diagnosis or medical evaluation. "
            "Consult a licensed healthcare professional for clinical assessments."
        ),
    }
