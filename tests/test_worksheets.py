"""Unit tests for digital worksheets and therapeutic self-monitoring schemas."""
import unittest

from app import create_app
from core.database import db
from core.worksheets import WORKSHEET_METADATA, get_worksheet_definition
from models import User, WorksheetAssignment


class TestWorksheets(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_worksheet_definitions(self):
        for key in ["thought_record", "daily_diary", "behavioral_chain"]:
            defn = get_worksheet_definition(key)
            self.assertIsNotNone(defn)
            self.assertEqual(defn["key"], key)
            self.assertGreater(len(defn["sections"]), 0)

    def test_patient_self_guided_worksheet_workflow(self):
        patient = User.query.filter(User.role.in_(["patient", "user"])).first()

        with self.client.session_transaction() as sess:
            sess["user_id"] = patient.id
            sess["role"] = patient.role
            sess["username"] = patient.username

        # Start self-guided
        resp = self.client.post("/worksheets/start/daily_diary", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        assignment = WorksheetAssignment.query.filter_by(
            patient_id=patient.id, worksheet_key="daily_diary"
        ).order_by(WorksheetAssignment.id.desc()).first()

        self.assertIsNotNone(assignment)
        self.assertFalse(assignment.is_completed)

        # Submit worksheet
        submit_resp = self.client.post(
            f"/worksheets/{assignment.id}/submit",
            data={
                "entry_date": "2026-10-14",
                "distress_sadness": "1 - Minimal",
                "distress_anxiety": "2 - Mild",
                "distress_anger": "0 - None",
                "target_urges": "Urge to withdraw",
                "skills_used": "STOP Skill (Stop, Take a step back, Observe, Proceed mindfully)",
                "skill_effectiveness": "4 - Very helpful",
                "daily_win": "Completed walking and deep breathing exercise",
            },
            follow_redirects=True,
        )
        self.assertEqual(submit_resp.status_code, 200)

        db.session.refresh(assignment)
        self.assertTrue(assignment.is_completed)
        self.assertIn("distress_anxiety", assignment.responses)


if __name__ == "__main__":
    unittest.main()
