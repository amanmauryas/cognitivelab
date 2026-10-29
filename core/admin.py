import csv
from collections import Counter
from datetime import datetime, timedelta
from io import StringIO

from flask import Blueprint, Response, flash, redirect, render_template, request, session, url_for
from core.database import db
from models import DiagnosticAssessment, TestSession, TestTrial, User, WorksheetAssignment

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def require_admin():
    """Verify that current session belongs to an authenticated admin user."""
    admin_id = session.get("user_id")
    admin = db.session.get(User, admin_id) if admin_id else None
    if not admin:
        session.clear()
        return None
    if admin.role != "admin":
        return None
    return admin


@admin_bp.route("/dashboard")
def dashboard():
    admin = require_admin()
    if not admin:
        flash("You do not have administrative privileges.", "error")
        return redirect(url_for("login"))

    cognitive_results = TestSession.query.order_by(TestSession.started_at.desc()).all()
    completed_cognitive = [r for r in cognitive_results if r.completed_at]

    diagnostic_results = DiagnosticAssessment.query.order_by(DiagnosticAssessment.completed_at.desc()).all()
    worksheet_results = WorksheetAssignment.query.order_by(WorksheetAssignment.assigned_at.desc()).all()
    total_users = User.query.count()

    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    collection_summary = {
        "patients": User.query.filter(User.role.in_(["patient", "user"])).count(),
        "total_users": total_users,
        "completed_sessions": len(completed_cognitive),
        "total_diagnostics": len(diagnostic_results),
        "total_worksheets": len(worksheet_results),
        "sessions_last_week": sum(
            r.completed_at >= recent_cutoff for r in completed_cognitive
        ),
        "completion_rate": round(
            (len(completed_cognitive) / len(cognitive_results) * 100) if cognitive_results else 0, 1
        ),
    }

    test_breakdown = Counter(r.test_type for r in completed_cognitive)
    diagnostic_breakdown = Counter(d.scale_name for d in diagnostic_results)

    return render_template(
        "admin.html",
        user=admin,
        results=cognitive_results,
        diagnostic_results=diagnostic_results,
        worksheet_results=worksheet_results,
        collection_summary=collection_summary,
        test_breakdown=test_breakdown,
        diagnostic_breakdown=diagnostic_breakdown,
    )


@admin_bp.route("/users")
def users():
    admin = require_admin()
    if not admin:
        flash("You do not have administrative privileges.", "error")
        return redirect(url_for("login"))

    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("users.html", user=admin, users=all_users)


@admin_bp.route("/export/sessions.csv")
def export_sessions():
    admin = require_admin()
    if not admin:
        flash("You do not have administrative privileges.", "error")
        return redirect(url_for("login"))

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "session_id", "participant_id", "username", "test_type", "test_version",
        "total_trials", "started_at", "completed_at", "accuracy", "mean_rt_ms",
        "median_rt_ms", "stroop_effect_ms",
    ])
    sessions = TestSession.query.order_by(TestSession.started_at.desc()).all()
    for test_session in sessions:
        metrics = test_session.summary_metrics or {}
        writer.writerow([
            test_session.id,
            test_session.user.participant_id if test_session.user else "",
            test_session.user.username if test_session.user else "",
            test_session.test_type,
            test_session.test_version or "",
            test_session.total_trials,
            test_session.started_at.isoformat() if test_session.started_at else "",
            test_session.completed_at.isoformat() if test_session.completed_at else "",
            metrics.get("accuracy", ""),
            metrics.get("mean_rt", ""),
            metrics.get("median_rt", ""),
            metrics.get("stroop_effect", ""),
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=session-data.csv"},
    )


@admin_bp.route("/export/diagnostics.csv")
def export_diagnostics():
    admin = require_admin()
    if not admin:
        flash("You do not have administrative privileges.", "error")
        return redirect(url_for("login"))

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "assessment_id", "participant_id", "username", "scale_id", "scale_name",
        "total_score", "max_score", "interpretation", "completed_at",
    ])
    assessments = DiagnosticAssessment.query.order_by(DiagnosticAssessment.completed_at.desc()).all()
    for d in assessments:
        writer.writerow([
            d.id,
            d.user.participant_id if d.user else "",
            d.user.username if d.user else "",
            d.scale_id,
            d.scale_name,
            d.total_score,
            d.max_score,
            d.interpretation or "",
            d.completed_at.isoformat() if d.completed_at else "",
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=diagnostic-data.csv"},
    )


# =========================================================================
# GRANULAR RECORD DELETION
# =========================================================================

@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    admin = require_admin()
    if not admin:
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    target_user = db.session.get(User, user_id)
    if not target_user:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))

    if target_user.id == admin.id:
        flash("You cannot delete your own admin account.", "error")
        return redirect(url_for("admin.users"))

    username = target_user.username
    db.session.delete(target_user)
    db.session.commit()

    flash(f"User '{username}' and all related data deleted successfully.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/sessions/<int:session_id>/delete", methods=["POST"])
def delete_session(session_id):
    admin = require_admin()
    if not admin:
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    target_session = db.session.get(TestSession, session_id)
    if not target_session:
        flash("Test session not found.", "error")
        return redirect(url_for("admin.dashboard"))

    db.session.delete(target_session)
    db.session.commit()

    flash(f"Cognitive test session #{session_id} and its trials deleted successfully.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/diagnostics/<int:assessment_id>/delete", methods=["POST"])
def delete_diagnostic(assessment_id):
    admin = require_admin()
    if not admin:
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    target_assessment = db.session.get(DiagnosticAssessment, assessment_id)
    if not target_assessment:
        flash("Diagnostic assessment not found.", "error")
        return redirect(url_for("admin.dashboard"))

    scale_name = target_assessment.scale_name
    db.session.delete(target_assessment)
    db.session.commit()

    flash(f"Diagnostic assessment #{assessment_id} ({scale_name}) deleted successfully.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/worksheets/<int:assignment_id>/delete", methods=["POST"])
def delete_worksheet(assignment_id):
    admin = require_admin()
    if not admin:
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    target_assignment = db.session.get(WorksheetAssignment, assignment_id)
    if not target_assignment:
        flash("Worksheet assignment not found.", "error")
        return redirect(url_for("admin.dashboard"))

    name = target_assignment.worksheet_name
    db.session.delete(target_assignment)
    db.session.commit()

    flash(f"Worksheet assignment '{name}' deleted successfully.", "success")
    return redirect(url_for("admin.dashboard"))


# =========================================================================
# SELECTIVE CATEGORY PURGE / BULK DELETE
# =========================================================================

@admin_bp.route("/purge/<category>", methods=["POST"])
def purge_category(category):
    admin = require_admin()
    if not admin:
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    try:
        if category == "cognitive":
            deleted_trials = TestTrial.query.delete()
            deleted_sessions = TestSession.query.delete()
            db.session.commit()
            flash(f"Purged all cognitive test data ({deleted_sessions} sessions, {deleted_trials} trials).", "success")

        elif category == "diagnostics":
            deleted_count = DiagnosticAssessment.query.delete()
            db.session.commit()
            flash(f"Purged all diagnostic scale assessments ({deleted_count} records).", "success")

        elif category == "worksheets":
            deleted_count = WorksheetAssignment.query.delete()
            db.session.commit()
            flash(f"Purged all worksheet assignments ({deleted_count} records).", "success")

        elif category == "test_users":
            # Delete only test patients/users, preserving admin and psychologist accounts
            users_to_delete = User.query.filter(User.role.in_(["patient", "user"])).all()
            count = len(users_to_delete)
            for u in users_to_delete:
                db.session.delete(u)
            db.session.commit()
            flash(f"Purged {count} participant/patient accounts.", "success")

        else:
            flash(f"Unknown purge category: '{category}'.", "error")

    except Exception as e:
        db.session.rollback()
        flash(f"Error purging data: {str(e)}", "error")

    return redirect(url_for("admin.dashboard"))
