from werkzeug.security import check_password_hash, generate_password_hash

from core.database import db


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum("admin", "psychologist", "patient", "user", name="user_role_enum"),
        nullable=False,
        default="patient",
    )
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(
        db.Enum("male", "female", "prefer_not_to_say", "other", name="gender"),
        nullable=False,
    )
    participant_id = db.Column(db.String(120), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    test_sessions = db.relationship("TestSession", back_populates="user", cascade="all, delete-orphan")
    worksheet_assignments = db.relationship(
        "WorksheetAssignment",
        foreign_keys="WorksheetAssignment.patient_id",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
