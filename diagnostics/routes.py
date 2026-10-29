"""Routes for administering, viewing, and scoring diagnostic questionnaires."""
from __future__ import annotations

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for

from core.catalog import DIAGNOSTIC_SCALES
from core.database import db
from models import DiagnosticAssessment, User
from .engine import list_available_scales, load_scale_definition, validate_responses
from .scoring import score_assessment

diagnostics_bp = Blueprint("diagnostics", __name__, url_prefix="/diagnostic-scales")


@diagnostics_bp.route("/")
@diagnostics_bp.route("/diagnostic-scales")
def index():
    """List available and planned diagnostic scales."""
    available = {s["id"]: s for s in list_available_scales()}
    scales = []

    for item in DIAGNOSTIC_SCALES:
        scale_id = item["id"]
        if scale_id in available:
            scales.append({
                **item,
                "status": "available",
                "title": available[scale_id].get("title", item["name"]),
                "description": available[scale_id].get("description", ""),
            })
        else:
            scales.append(item)

    return render_template("diagnostics/index.html", scales=scales)


@diagnostics_bp.route("/<scale_id>")
def take(scale_id: str):
    """Render questionnaire administration form for a given scale."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to complete diagnostic questionnaires.", "error")
        return redirect(url_for("login"))

    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        flash("User not found.", "error")
        return redirect(url_for("login"))

    definition = load_scale_definition(scale_id)
    if not definition:
        abort(404, description=f"Diagnostic scale '{scale_id}' not found.")

    return render_template("diagnostics/take.html", scale=definition, user=user)


@diagnostics_bp.route("/<scale_id>/submit", methods=["POST"])
def submit(scale_id: str):
    """Process and score questionnaire responses."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    user = db.session.get(User, user_id)
    if not user:
        flash("User session invalid.", "error")
        return redirect(url_for("login"))

    definition = load_scale_definition(scale_id)
    if not definition:
        abort(404, description="Diagnostic scale not found.")

    # Collect answers from form submission or JSON payload
    if request.is_json:
        responses = request.get_json().get("responses", {})
    else:
        responses = {}
        for q in definition.get("questions", []):
            q_id = q.get("id")
            val = request.form.get(q_id)
            if val is not None:
                responses[q_id] = int(val)

    # Validate responses
    is_valid, error_msg = validate_responses(definition, responses)
    if not is_valid:
        flash(error_msg, "error")
        return render_template("diagnostics/take.html", scale=definition, user=user, current_responses=responses)

    # Score assessment
    score_result = score_assessment(definition, responses)

    # Persist in database
    assessment = DiagnosticAssessment(
        user_id=user.id,
        scale_id=definition["id"],
        scale_name=f"{definition.get('name', definition['id'].upper())} - {definition.get('title', '')}".strip(" -"),
        total_score=score_result["total_score"],
        max_score=score_result["max_score"],
        interpretation=score_result["interpretation"],
        responses=responses,
        summary_metrics=score_result,
    )
    db.session.add(assessment)
    db.session.commit()

    if request.is_json:
        return jsonify({"success": True, "assessment_id": assessment.id, "result": score_result}), 201

    return render_template("diagnostics/result.html", result=score_result, assessment=assessment, user=user)


@diagnostics_bp.route("/<scale_id>.json")
@diagnostics_bp.route("/api/<scale_id>")
def scale_json(scale_id: str):
    """Return declarative JSON schema for questionnaire client engines."""
    definition = load_scale_definition(scale_id)
    if not definition:
        return jsonify({"error": f"Scale '{scale_id}' not found"}), 404
    return jsonify(definition)