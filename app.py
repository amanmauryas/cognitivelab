from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.templating import DispatchingJinjaLoader

from core.database import User, TestSession, TestTrial, db, init_db
from core.admin import admin_bp
from tests.stroop import stroop_bp

BASE_DIR = Path(__file__).resolve().parent


class BlueprintAwareDispatchingJinjaLoader(DispatchingJinjaLoader):
    def _iter_loaders(self, template: str):
        if request and request.blueprint and request.blueprint in self.app.blueprints:
            bp = self.app.blueprints[request.blueprint]
            if bp.jinja_loader is not None:
                yield bp, bp.jinja_loader
        yield from super()._iter_loaders(template)


def normalize_username(username: str) -> str:
    return username.strip().lower()


def generate_participant_id(name: str, gender: str) -> str:
    name_initial = name.strip()[:1].upper()
    gender_initial = gender.strip()[:1].upper()
    date_code = datetime.now().strftime("%y%m")
    monthly_count = User.query.filter(
        User.participant_id.like(f"__{date_code}%")
    ).count()

    serial_no = f"{monthly_count + 1:04d}"
    return f"{name_initial}{gender_initial}{date_code}{serial_no}"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-stroop-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{BASE_DIR / 'data' / 'psychometrics.db'}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.jinja_options = {
        **app.jinja_options,
        "loader": BlueprintAwareDispatchingJinjaLoader(app)
    }

    init_db(app)

    app.register_blueprint(stroop_bp)
    app.register_blueprint(admin_bp)

    @app.route("/create_admin")
    def create_admin():
        existing_admin = User.query.filter_by(
            username="admin"
        ).first()

        if existing_admin:
            flash("Admin already exists.", "info")
            return redirect(url_for("index"))

        admin = User(
            name="Admin",
            role="admin",
            username="admin",
            age=22,
            gender="prefer_not_to_say",
            participant_id="MASTERADMIN1234",
        )

        # Hash password before storing
        admin.set_password("Masteradmin1234")
        db.session.add(admin)
        db.session.commit()
        flash("Admin created successfully.", "success")

        return redirect(url_for("index"))

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            username = normalize_username(
                request.form.get("username", "")
            )

            age = request.form.get("age", "").strip()
            role = request.form.get("role", "").strip()
            gender = request.form.get("gender", "").strip()
            password = request.form.get("password", "")
            consent = request.form.get("consent")

            if not all([
                name,
                username,
                age,
                gender,
                role,
                password,
                consent
            ]):
                flash("Please complete all required fields.", "error")
                return render_template("register.html")

            existing_user = User.query.filter_by(
                username=username
            ).first()

            if existing_user:
                flash("That username is already taken. Choose another username.", "error")
                return render_template("register.html")

            try:
                age_value = int(age)
                if age_value <= 0 or age_value > 120:
                    raise ValueError
            except ValueError:
                flash("Please enter a valid age.", "error")
                return render_template("register.html")

            participant_id = generate_participant_id(name, gender)

            user = User(
                name=name,
                username=username,
                age=age_value,
                gender=gender,
                role=role,
                participant_id=participant_id,
            )

            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            session["user_id"] = user.id
            session["username"] = user.username
            session["participant_id"] = user.participant_id
            session["role"] = user.role

            flash(
                f"Registration complete. Your participant ID is {participant_id}.",
                "success"
            )

            return redirect(url_for("stroop.test"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = normalize_username(
                request.form.get("username", "")
            )
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()
            if not user or not user.check_password(password):
                flash("Invalid username or password.", "error")
                return render_template("login.html")

            session["user_id"] = user.id
            session["role"] = user.role
            session["username"] = user.username
            session["participant_id"] = user.participant_id

            flash(
                f"Logged in as {user.username}.",
                "success"
            )

            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))

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
            TestSession.query
            .filter_by(user_id=user.id)
            .order_by(TestSession.completed_at.desc())
            .all()
        )

        return render_template(
            "profile.html",
            user=user,
            results=results
        )

    @app.route("/seed")
    def seed():
        if User.query.filter_by(username="dummy1").first():
            return "Dummy data already exists"

        users_data = [
            {
                "name": "Dummy User 1",
                "username": "dummy1",
                "age": 22,
                "gender": "male",
                "participant_id": "DM26080001",
                "accuracy": 95.0,
                "mean_rt": 650.5
            },
            {
                "name": "Dummy User 2",
                "username": "dummy2",
                "age": 25,
                "gender": "female",
                "participant_id": "DF26080002",
                "accuracy": 87.0,
                "mean_rt": 780.3
            }
        ]

        for user_data in users_data:
            user = User(
                name=user_data["name"],
                username=user_data["username"],
                age=user_data["age"],
                gender=user_data["gender"],
                participant_id=user_data["participant_id"]
            )
            user.set_password("password123")
            db.session.add(user)
            db.session.flush()

            test_session = TestSession(
                user_id=user.id,
                test_type="stroop",
                test_version="v1",
                total_trials=5,
                summary_metrics={
                    "accuracy": user_data["accuracy"],
                    "mean_rt": user_data["mean_rt"],
                    "median_rt": user_data["mean_rt"] - 20,
                    "std_rt": 85.5,
                    "error_rate": 100 - user_data["accuracy"],
                    "congruent_accuracy": 98.0,
                    "incongruent_accuracy": user_data["accuracy"] - 5,
                    "congruent_mean_rt": user_data["mean_rt"] - 60,
                    "incongruent_mean_rt": user_data["mean_rt"] + 60,
                    "accuracy_interference": 5.0,
                    "stroop_effect": 120.0
                },
                test_config={
                    "practice_trials": 10,
                    "experimental_trials": 5
                },
                completed_at=datetime.utcnow()
            )

            db.session.add(test_session)
            db.session.flush()

            trials = [
                ("RED", "red", True, "red", 520.4, True),
                ("BLUE", "green", False, "green", 710.2, True),
                ("GREEN", "blue", False, "blue", 680.8, True),
                ("YELLOW", "yellow", True, "yellow", 590.1, True),
                ("RED", "blue", False, "red", 830.5, False)
            ]

            for trial_number, (word, color, congruent, response, rt, correct) in enumerate(trials, start=1):
                test_trial = TestTrial(
                    test_session_id=test_session.id,
                    trial_number=trial_number,
                    stimulus={
                        "word": word,
                        "color": color,
                        "congruent": congruent
                    },
                    response={
                        "selected_color": response,
                        "correct": correct
                    },
                    response_time=rt,
                    correct=correct
                )
                db.session.add(test_trial)

        db.session.commit()
        return "2 dummy users and Stroop test data created successfully"

    @app.route("/coming-soon")
    def coming_soon():
        return render_template("coming_soon.html")

    @app.route("/soft_tools")
    def soft_tools():
        return render_template("soft_tools.html")

    return app


if __name__ == "__main__":
    app = create_app()
<<<<<<< HEAD
    app.run(debug=True)
=======
    app.run()
>>>>>>> 6a7b3c8da9175664f4039cb481436329f358747e
