"""Unit tests for cognitive Stroop scoring and metric calculations."""
import unittest

from cognitive.stroop.scoring import compute_stroop_metrics


class TestStroopScoring(unittest.TestCase):
    def test_empty_trials(self):
        result = compute_stroop_metrics([])
        self.assertEqual(result["total_trials"], 0)
        self.assertEqual(result["accuracy"], 0.0)

    def test_congruent_and_incongruent_scoring(self):
        trials = [
            {"congruent": True, "correct": True, "rt": 500.0},
            {"congruent": True, "correct": True, "rt": 600.0},
            {"congruent": False, "correct": True, "rt": 700.0},
            {"congruent": False, "correct": False, "rt": 900.0},
        ]
        metrics = compute_stroop_metrics(trials)

        self.assertEqual(metrics["total_trials"], 4)
        self.assertEqual(metrics["accuracy"], 75.0)  # 3 of 4 correct
        self.assertEqual(metrics["congruent_accuracy"], 100.0)
        self.assertEqual(metrics["incongruent_accuracy"], 50.0)
        self.assertEqual(metrics["congruent_mean_rt"], 550.0)
        self.assertEqual(metrics["incongruent_mean_rt"], 700.0)  # Only correct trial counted for RT
        self.assertEqual(metrics["stroop_effect"], 150.0)  # 700 - 550


if __name__ == "__main__":
    unittest.main()
