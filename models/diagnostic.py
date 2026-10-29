"""Diagnostic assessment persistence models.

Stores completed questionnaire submissions and clinical scoring outcomes.
"""
from __future__ import annotations

from core.database import db


class DiagnosticAssessment(db.Model):
    """Stores individual completed diagnostic questionnaire responses and scores."""

    __tablename__ = "diagnostic_assessment"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    scale_id = db.Column(db.String(50), nullable=False, index=True)
    scale_name = db.Column(db.String(100), nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, nullable=False, default=27)
    interpretation = db.Column(db.String(100), nullable=True)
    responses = db.Column(db.JSON, nullable=True)
    summary_metrics = db.Column(db.JSON, nullable=True)
    completed_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", backref=db.backref("diagnostic_assessments", lazy="dynamic", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scale_id": self.scale_id,
            "scale_name": self.scale_name,
            "total_score": self.total_score,
            "max_score": self.max_score,
            "interpretation": self.interpretation,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
