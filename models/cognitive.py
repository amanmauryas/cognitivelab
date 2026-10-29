from core.database import db


class TestSession(db.Model):
    """Existing cognitive-session table; table name is preserved for SQLite compatibility."""

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
    """Existing cognitive-trial table; table name is preserved for SQLite compatibility."""

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
