from __future__ import annotations

import os
import webbrowser
from datetime import datetime
from pathlib import Path
from threading import Timer

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from models.database import TestResult, User, db, init_db


BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-stroop-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'data' / 'psychometrics.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

init_db(app)

from routes.stroop import stroop_bp
app.register_blueprint(stroop_bp)


def normalize_username(username: str) -> str:
    return username.strip().lower()


def generate_participant_id(name: str, gender: str) -> str:
    name_initial = name.strip()[:1].upper()
    gender_initial = gender.strip()[:1].upper()
    date_code = datetime.now().strftime("%y%m")
    monthly_count = User.query.filter(User.participant_id.like(f"__{date_code}%")).count()
    serial_no = f"{monthly_count + 1:04d}"

    return f"{name_initial}{gender_initial}{date_code}{serial_no}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = normalize_username(request.form.get("username", ""))
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        consent = request.form.get("consent")

        if not all([name, username, age, gender, consent]):
            flash("Please complete all required fields.", "error")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("That username is already taken. Choose another username.", "error")
            return render_template("register.html")

        try:
            age_value = int(age)
        except ValueError:
            flash("Please enter a valid age.", "error")
            return render_template("register.html")

        participant_id = generate_participant_id(name, gender)
        user = User(
            name=name,
            username=username,
            age=age_value,
            gender=gender,
            participant_id=participant_id,
        )
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["username"] = user.username
        session["participant_id"] = user.participant_id
        flash(f"Registration complete. Your participant ID is {participant_id}.", "success")
        return redirect(url_for('stroop.test'))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = normalize_username(request.form.get("username", ""))
        user = User.query.filter_by(username=username).first()

        if not user:
            flash("No participant was found with that username.", "error")
            return render_template("login.html")

        session["user_id"] = user.id
        session["username"] = user.username
        session["participant_id"] = user.participant_id
        flash(f"Logged in as {user.username}.", "success")
        return redirect(url_for("stroop.test"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))




@app.route("/profile")
def profile():
    user_id = session.get("user_id")

    if not user_id:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    user = db.session.get(User, user_id)

    if not user:
        session.clear()
        flash("User not found.", "error")
        return redirect(url_for("login"))

    results = (
        TestResult.query.filter_by(user_id=user.id)
        .order_by(TestResult.created_at.desc())
        .all()
    )
    return render_template("profile.html", user=user, results=results)


@app.route("/coming-soon")
def coming_soon():
    return render_template("coming_soon.html")


if __name__ == "__main__":
    url = "http://127.0.0.1:5000/"

    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(debug=True)
