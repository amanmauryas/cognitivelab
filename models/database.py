from __future__ import annotations

from pathlib import Path

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(
        db.Enum("male", "female", "prefer_not_to_say", "other", name="gender"),
        nullable=False,
    )
    participant_id = db.Column(db.String(120), nullable=False, unique=True, index=True)


class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    test_name = db.Column(db.String(80), nullable=False, default="Stroop Task")
    accuracy = db.Column(db.Float, nullable=False)
    mean_rt = db.Column(db.Float, nullable=False)
    total_trials = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", backref="results")


def init_db(app):
    data_dir = Path(app.instance_path).parent / "data"
    data_dir.mkdir(exist_ok=True)

    db.init_app(app)
    with app.app_context():
        db.create_all()
