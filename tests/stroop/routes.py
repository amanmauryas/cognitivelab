from datetime import datetime
from flask import flash, jsonify, redirect, render_template, request, session, url_for

from core.database import User, TestSession, TestTrial, db
from . import stroop_bp


@stroop_bp.route("/test/stroop/")
@stroop_bp.route("/test/stroop")
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

    return render_template("index.html", user=user)


@stroop_bp.route("/test/stroop/result", methods=["POST"])
def save_test_result():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"saved": False, "error": "Login required"}), 401

    data = request.get_json()

    if not data:
        return jsonify({"saved": False, "error": "No data received"}), 400

    trials = data.get("trials", [])

    if not trials:
        return jsonify({"saved": False, "error": "No trial data received"}), 400

    try:
        test_session = TestSession(
            user_id=user_id,
            test_type="stroop",
            test_version="v1",
            total_trials=len(trials),
            summary_metrics={
                "accuracy": float(data.get("accuracy", 0)),
                "mean_rt": float(data.get("mean_rt", 0)),
                "median_rt": float(data.get("median_rt", 0)),
                "std_rt": float(data.get("std_rt", 0)),
                "error_rate": float(data.get("error_rate", 0)),
                "congruent_accuracy": float(data.get("congruent_accuracy", 0)),
                "incongruent_accuracy": float(data.get("incongruent_accuracy", 0)),
                "congruent_mean_rt": float(data.get("congruent_mean_rt", 0)),
                "incongruent_mean_rt": float(data.get("incongruent_mean_rt", 0)),
                "accuracy_interference": float(data.get("accuracy_interference", 0)),
                "stroop_effect": float(data.get("stroop_effect", 0)),
            },
            test_config={
                "practice_trials": 10,
                "experimental_trials": len(trials),
                "fixation_duration_ms": 500,
                "inter_trial_interval_ms": 300,
                "colors": [
                    "red",
                    "blue",
                    "green",
                    "yellow",
                ],
                "response_keys": {
                    "r": "red",
                    "b": "blue",
                    "g": "green",
                    "y": "yellow",
                },
            },
            completed_at=datetime.utcnow(),
        )

        db.session.add(test_session)
        db.session.flush()

        for trial_number, trial in enumerate(trials, start=1):
            if not isinstance(trial, dict):
                continue

            test_trial = TestTrial(
                test_session_id=test_session.id,
                trial_number=trial_number,
                stimulus={
                    "word": trial.get("word"),
                    "color": trial.get("color"),
                    "congruent": trial.get("congruent", False),
                },
                response={
                    "selected_color": trial.get("response"),
                    "correct": trial.get("correct", False),
                },
                response_time=float(trial.get("rt", 0)),
                correct=bool(trial.get("correct", False)),
            )

            db.session.add(test_trial)

        db.session.commit()

        return jsonify({
            "saved": True,
            "session_id": test_session.id,
            "total_trials": len(trials),
        }), 201

    except (ValueError, TypeError) as error:
        db.session.rollback()
        return jsonify({
            "saved": False,
            "error": f"Invalid data: {str(error)}"
        }), 400

    except Exception as error:
        db.session.rollback()
        print(f"Error saving Stroop result: {error}")
        return jsonify({
            "saved": False,
            "error": "Failed to save test result"
        }), 500
