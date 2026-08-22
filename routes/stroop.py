from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from models.database import TestResult, User, db

stroop_bp = Blueprint("stroop", __name__, url_prefix="/test/stroop")


@stroop_bp.route("/")
def test():
    user_id = session.get("user_id")

    if not user_id:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))
    
    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        flash("User not found.", "error")
        return redirect(url_for("login"))

    return render_template("stroop.html", user=user)


@stroop_bp.route("/result", methods=["POST"])
def save_test_result():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "login required"}), 401

    data = request.get_json() or {}
    result = TestResult(
        user_id=user_id,
        test_name="Stroop Task",
        accuracy=float(data.get("accuracy", 0)),
        mean_rt=float(data.get("mean_rt", 0)),
        total_trials=int(data.get("total_trials", 0)),
    )
    db.session.add(result)
    db.session.commit()
    return jsonify({"saved": True})
