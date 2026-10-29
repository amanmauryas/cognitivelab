from core.database import db


class WorksheetAssignment(db.Model):
    __tablename__ = "worksheet_assignment"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    worksheet_key = db.Column(db.String(50), nullable=True, index=True)
    worksheet_name = db.Column(db.String(120), nullable=False)
    responses = db.Column(db.JSON, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    assigned_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    patient = db.relationship("User", foreign_keys=[patient_id], back_populates="worksheet_assignments")
    assigned_by = db.relationship("User", foreign_keys=[assigned_by_id])

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None
