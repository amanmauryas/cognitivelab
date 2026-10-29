"""Report logging and persistence models.

Stores generated test summary reports, clinical digests, and export records.
"""
from __future__ import annotations

from core.database import db


class ReportRecord(db.Model):
    """Stores generated report logs and metadata."""

    __tablename__ = "report_record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    report_type = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    metrics_snapshot = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", backref=db.backref("reports", lazy="dynamic", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "report_type": self.report_type,
            "title": self.title,
            "summary": self.summary,
            "metrics_snapshot": self.metrics_snapshot,
            "created_at": self.completed_at.isoformat() if hasattr(self, "completed_at") else self.created_at.isoformat(),
        }
