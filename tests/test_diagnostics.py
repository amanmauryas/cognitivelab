"""Unit tests for diagnostic scale loader, validator, scoring engine, and admin deletions."""
import unittest

from app import create_app
from core.database import db
from diagnostics.engine import list_available_scales, load_scale_definition, validate_responses
from diagnostics.scoring import score_assessment
from models import DiagnosticAssessment, TestSession, User


class TestDiagnosticsEngine(unittest.TestCase):
    def test_load_all_definitions(self):
        for scale_id in ["phq9", "gad7", "ybocs"]:
            defn = load_scale_definition(scale_id)
            self.assertIsNotNone(defn, f"Scale '{scale_id}' should load")
            self.assertEqual(defn["id"], scale_id)
            self.assertGreater(len(defn["questions"]), 0)

    def test_list_available_scales(self):
        scales = list_available_scales()
        scale_ids = {s["id"] for s in scales}
        self.assertTrue({"phq9", "gad7", "ybocs"}.issubset(scale_ids))

    def test_gad7_scoring(self):
        gad7 = load_scale_definition("gad7")
        self.assertEqual(len(gad7["questions"]), 7)
        # Moderate anxiety test (all 2s -> 14)
        responses = {q["id"]: 2 for q in gad7["questions"]}
        res = score_assessment(gad7, responses)
        self.assertEqual(res["total_score"], 14)
        self.assertEqual(res["interpretation"], "Moderate anxiety")

    def test_ybocs_scoring(self):
        ybocs = load_scale_definition("ybocs")
        self.assertEqual(len(ybocs["questions"]), 10)
        # Severe symptoms test (all 3s -> 30)
        responses = {q["id"]: 3 for q in ybocs["questions"]}
        res = score_assessment(ybocs, responses)
        self.assertEqual(res["total_score"], 30)
        self.assertEqual(res["interpretation"], "Severe symptoms")

    def test_validate_responses_complete(self):
        phq9 = load_scale_definition("phq9")
        responses = {q["id"]: 1 for q in phq9["questions"]}
        is_valid, err = validate_responses(phq9, responses)
        self.assertTrue(is_valid)
        self.assertIsNone(err)

    def test_validate_responses_missing(self):
        phq9 = load_scale_definition("phq9")
        responses = {"phq9_01": 1}
        is_valid, err = validate_responses(phq9, responses)
        self.assertFalse(is_valid)
        self.assertIn("Missing response", err)


class TestAdminDeleteOperations(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_admin_delete_assessment(self):
        admin = User.query.filter_by(role="admin").first()
        user = User.query.filter(User.role.in_(["patient", "user"])).first()

        assessment = DiagnosticAssessment(
            user_id=user.id,
            scale_id="phq9",
            scale_name="PHQ-9 Test",
            total_score=10,
            max_score=27,
            interpretation="Moderate",
        )
        db.session.add(assessment)
        db.session.commit()
        assessment_id = assessment.id

        with self.client.session_transaction() as sess:
            sess["user_id"] = admin.id
            sess["role"] = "admin"

        del_resp = self.client.post(f"/admin/diagnostics/{assessment_id}/delete", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        self.assertIsNone(db.session.get(DiagnosticAssessment, assessment_id))


if __name__ == "__main__":
    unittest.main()
