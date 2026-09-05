from __future__ import annotations
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "psychologist", "user", name="user_role_enum"), nullable=False, default="user")
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.Enum("male", "female", "prefer_not_to_say", "other", name="gender"), nullable=False)
    participant_id = db.Column(db.String(120), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    test_sessions = db.relationship("TestSession", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class TestSession(db.Model):
    __tablename__ = "test_session"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    test_type = db.Column(db.String(100), nullable=False, index=True)
    test_version = db.Column(db.String(50), nullable=True)
    total_trials = db.Column(db.Integer, nullable=False, default=0)
    summary_metrics = db.Column(db.JSON, nullable=True)
    test_config = db.Column(db.JSON, nullable=True)
    started_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship("User", back_populates="test_sessions")
    trials = db.relationship("TestTrial", back_populates="test_session", cascade="all, delete-orphan", order_by="TestTrial.trial_number")


class TestTrial(db.Model):
    __tablename__ = "test_trial"
    
    id = db.Column(db.Integer, primary_key=True)
    test_session_id = db.Column(db.Integer, db.ForeignKey("test_session.id"), nullable=False, index=True)
    trial_number = db.Column(db.Integer, nullable=False)
    stimulus = db.Column(db.JSON, nullable=True)
    response = db.Column(db.JSON, nullable=True)
    response_time = db.Column(db.Float, nullable=True)
    correct = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    test_session = db.relationship("TestSession", back_populates="trials")
    
    __table_args__ = (db.UniqueConstraint("test_session_id", "trial_number", name="unique_trial_per_session"),)


def init_db(app):
    db.init_app(app)

    with app.app_context():
        db.create_all(checkfirst=True)
