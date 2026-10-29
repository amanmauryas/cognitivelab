from __future__ import annotations

from datetime import datetime

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

from config import Config
from core.auth import is_patient_role, normalize_username
from core.catalog import COGNITIVE_TASKS, DIAGNOSTIC_SCALES, WORKSHEETS
from core.worksheets import WORKSHEET_METADATA, get_worksheet_definition
from core.database import db, init_db
from core.utils import generate_participant_id
from models import DiagnosticAssessment, TestSession, TestTrial, User, WorksheetAssignment
from core.admin import admin_bp
from cognitive.stroop import stroop_bp
from diagnostics.routes import diagnostics_bp


class BlueprintAwareDispatchingJinjaLoader(DispatchingJinjaLoader):
    def _iter_loaders(self, template: str):
        if request and request.blueprint and request.blueprint in self.app.blueprints:
            bp = self.app.blueprints[request.blueprint]
            if bp.jinja_loader is not None:
                yield bp, bp.jinja_loader
        yield from super()._iter_loaders(template)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.jinja_options = {
        **app.jinja_options,
        "loader": BlueprintAwareDispatchingJinjaLoader(app)
    }

    init_db(app)

    app.register_blueprint(stroop_bp)
    app.register_blueprint(diagnostics_bp)
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
        return render_template(
            "soft_tools.html",
            cognitive_tasks=COGNITIVE_TASKS,
            diagnostic_scales=DIAGNOSTIC_SCALES,
        )

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

            if role not in {"patient", "psychologist"}:
                flash("Please choose a valid registration role.", "error")
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

            monthly_count = User.query.filter(
                User.participant_id.like(f"__{datetime.now().strftime('%y%m')}%")
            ).count()
            participant_id = generate_participant_id(name, gender, monthly_count)

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

            if role == "psychologist":
                return redirect(url_for("psychologist_dashboard"))
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

            if user.role == "psychologist":
                return redirect(url_for("psychologist_dashboard"))

            return redirect(url_for("index"))

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

        diagnostic_results = (
            DiagnosticAssessment.query
            .filter_by(user_id=user.id)
            .order_by(DiagnosticAssessment.completed_at.desc())
            .all()
        )

        return render_template(
            "profile.html",
            user=user,
            results=results,
            diagnostic_results=diagnostic_results,
        )

    @app.route('/tech-intern')
    def intern():
        return render_template("aifeature.html")

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
        return redirect(url_for("index"))

    @app.route("/psychologist/dashboard")
    def psychologist_dashboard():
        psychologist_id = session.get("user_id")
        if not psychologist_id or session.get("role") != "psychologist":
            flash("Only psychologists can view the collection dashboard.", "error")
            return redirect(url_for("index"))

        patients = User.query.filter(User.role.in_(["patient", "user"])).order_by(User.name).all()
        completed_sessions = (
            TestSession.query.filter(TestSession.completed_at.isnot(None))
            .order_by(TestSession.completed_at.desc())
            .all()
        )
        assignments = (
            WorksheetAssignment.query.filter_by(assigned_by_id=psychologist_id)
            .order_by(WorksheetAssignment.assigned_at.desc())
            .limit(8)
            .all()
        )
        completed_diagnostics = (
            DiagnosticAssessment.query
            .order_by(DiagnosticAssessment.completed_at.desc())
            .all()
        )
        return render_template(
            "psychologist_dashboard.html",
            patients=patients,
            recent_sessions=completed_sessions[:8],
            recent_diagnostics=completed_diagnostics[:8],
            recent_assignments=assignments,
            completed_session_count=len(completed_sessions),
            completed_diagnostic_count=len(completed_diagnostics),
            cognitive_tasks=COGNITIVE_TASKS,
            diagnostic_scales=DIAGNOSTIC_SCALES,
        )

    @app.route("/worksheets")
    def patient_worksheets():
        user_id = session.get("user_id")
        if not user_id or not is_patient_role(session.get("role")):
            flash("Only patients can view assigned digital worksheets.", "error")
            return redirect(url_for("login"))
        assignments = WorksheetAssignment.query.filter_by(patient_id=user_id).order_by(WorksheetAssignment.assigned_at.desc()).all()
        return render_template("worksheets.html", assignments=assignments)

    @app.route("/psychologist/worksheets", methods=["GET", "POST"])
    def psychologist_worksheets():
        psychologist_id = session.get("user_id")
        if not psychologist_id or session.get("role") != "psychologist":
            flash("Only psychologists can assign digital worksheets.", "error")
            return redirect(url_for("index"))

        patients = User.query.filter(User.role.in_(["patient", "user"])).order_by(User.name).all()
        worksheet_options = dict(WORKSHEETS)
        if request.method == "POST":
            patient_id = request.form.get("patient_id", type=int)
            worksheet_key = request.form.get("worksheet")
            patient = db.session.get(User, patient_id)
            if not patient or not is_patient_role(patient.role) or worksheet_key not in worksheet_options:
                flash("Choose a valid patient and worksheet.", "error")
            else:
                db.session.add(WorksheetAssignment(patient_id=patient.id, assigned_by_id=psychologist_id, worksheet_name=worksheet_options[worksheet_key], worksheet_key=worksheet_key))
                db.session.commit()
                flash(f"{worksheet_options[worksheet_key]} assigned to {patient.name}.", "success")
                return redirect(url_for("psychologist_worksheets"))

        assignments = WorksheetAssignment.query.filter_by(assigned_by_id=psychologist_id).order_by(WorksheetAssignment.assigned_at.desc()).all()
        return render_template("psychologist_worksheets.html", patients=patients, assignments=assignments, worksheet_options=worksheet_options)


    @app.route("/worksheets/start/<worksheet_key>", methods=["POST"])
    def start_self_worksheet(worksheet_key: str):
        user_id = session.get("user_id")
        if not user_id or not is_patient_role(session.get("role")):
            flash("Please log in as a patient to access digital worksheets.", "error")
            return redirect(url_for("login"))

        worksheet_options = dict(WORKSHEETS)
        if worksheet_key not in worksheet_options:
            flash("Invalid worksheet type requested.", "error")
            return redirect(url_for("patient_worksheets"))

        assignment = WorksheetAssignment(
            patient_id=user_id,
            assigned_by_id=user_id,
            worksheet_key=worksheet_key,
            worksheet_name=worksheet_options[worksheet_key],
        )
        db.session.add(assignment)
        db.session.commit()
        return redirect(url_for("fill_worksheet", assignment_id=assignment.id))

    @app.route("/worksheets/<int:assignment_id>")
    def fill_worksheet(assignment_id: int):
        user_id = session.get("user_id")
        user_role = session.get("role")
        if not user_id:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))

        assignment = db.session.get(WorksheetAssignment, assignment_id)
        if not assignment:
            flash("Worksheet assignment not found.", "error")
            return redirect(url_for("patient_worksheets"))

        if is_patient_role(user_role) and assignment.patient_id != user_id:
            flash("Unauthorized access to this worksheet.", "error")
            return redirect(url_for("patient_worksheets"))

        key = assignment.worksheet_key
        if not key:
            for k, name in WORKSHEETS:
                if name.lower() in assignment.worksheet_name.lower():
                    key = k
                    break
            key = key or "thought_record"

        definition = get_worksheet_definition(key) or get_worksheet_definition("thought_record")
        edit_mode = request.args.get("edit") == "1"
        current_responses = assignment.responses or {}

        return render_template(
            "worksheet_form.html",
            assignment=assignment,
            definition=definition,
            current_responses=current_responses,
            edit_mode=edit_mode,
        )

    @app.route("/worksheets/<int:assignment_id>/submit", methods=["POST"])
    def submit_worksheet(assignment_id: int):
        user_id = session.get("user_id")
        user_role = session.get("role")
        if not user_id:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))

        assignment = db.session.get(WorksheetAssignment, assignment_id)
        if not assignment:
            flash("Worksheet assignment not found.", "error")
            return redirect(url_for("patient_worksheets"))

        if is_patient_role(user_role) and assignment.patient_id != user_id:
            flash("Unauthorized to submit this worksheet.", "error")
            return redirect(url_for("patient_worksheets"))

        responses = {}
        for key in request.form:
            values = request.form.getlist(key)
            if len(values) > 1:
                responses[key] = values
            else:
                responses[key] = request.form.get(key)

        assignment.responses = responses
        assignment.completed_at = datetime.utcnow()
        db.session.commit()

        flash(f"{assignment.worksheet_name} completed and saved successfully.", "success")
        return redirect(url_for("fill_worksheet", assignment_id=assignment.id))

    @app.route("/psychologist/worksheets/<int:assignment_id>/notes", methods=["POST"])
    def save_worksheet_notes(assignment_id: int):
        user_id = session.get("user_id")
        user_role = session.get("role")
        if not user_id or user_role not in ["psychologist", "admin"]:
            flash("Only clinicians can add clinical notes.", "error")
            return redirect(url_for("index"))

        assignment = db.session.get(WorksheetAssignment, assignment_id)
        if not assignment:
            flash("Worksheet not found.", "error")
            return redirect(url_for("psychologist_dashboard"))

        notes = request.form.get("notes", "").strip()
        assignment.notes = notes
        db.session.commit()

        flash("Clinical notes updated successfully.", "success")
        return redirect(url_for("fill_worksheet", assignment_id=assignment.id))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
