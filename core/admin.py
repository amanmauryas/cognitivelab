from flask import Blueprint, flash, redirect, render_template, session, url_for
from core.database import User, TestSession, db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None

    if not user:
        session.clear()
        flash("Unauthorized access or user not found.", "error")
        return redirect(url_for("login"))

    if user.role != "admin":
        flash("You do not have admin privileges.", "error")
        return redirect(url_for("login"))

    results = TestSession.query.order_by(TestSession.started_at.desc()).all()

    return render_template(
        "admin.html",
        user=user,
        results=results
    )

@admin_bp.route("/users")
def users():
    users = User.query.order_by(User.created_at.desc()).all()

    return render_template(
        "users.html",
        user=users,
        users=users
    )


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    admin_id = session.get("user_id")
    admin = db.session.get(User, admin_id) if admin_id else None

    if not admin:
        session.clear()
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    if admin.role != "admin":
        flash("You do not have admin privileges.", "error")
        return redirect(url_for("login"))

    user = db.session.get(User, user_id)

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))

    if user.id == admin.id:
        flash("You cannot delete your own admin account.", "error")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully.", "success")
    return redirect(url_for("admin.users"))
