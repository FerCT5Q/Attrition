from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECK_PATH = ROOT / "tools" / "build_distribution_html_v2.py"
SPEC = importlib.util.spec_from_file_location("above_average_team_turnover_deck_test", DECK_PATH)
assert SPEC is not None and SPEC.loader is not None
DECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DECK)


class AboveAverageTeamTurnoverTests(unittest.TestCase):
    def setUp(self):
        self.original_evidence = DECK.ABOVE_AVERAGE_TEAM_TURNOVER_EVIDENCE

    def tearDown(self):
        DECK.ABOVE_AVERAGE_TEAM_TURNOVER_EVIDENCE = self.original_evidence

    def test_loader_and_slide_use_frozen_presentation_safe_evidence(self):
        evidence = DECK.above_average_team_turnover_evidence()
        self.assertEqual(evidence["deliverable_mode"], "presentation")
        self.assertEqual(evidence["outcome"], "pass")
        self.assertEqual(
            {row["signal"] for row in evidence["distribution"]},
            {"0", "1", "Unknown"},
        )
        markup = DECK.above_average_team_turnover_slide(40)
        self.assertIn("Above-average team turnover", markup)
        self.assertIn("9.71%", markup)
        self.assertIn("12.62%", markup)
        self.assertIn("1.3", markup)
        self.assertIn("145 reports", markup)
        self.assertIn("Unknown", markup)
        self.assertNotIn("manager_employee_id", markup)

    def test_threshold_sensitivity_is_frozen_and_aggregate_only(self):
        evidence = DECK.above_average_team_turnover_sensitivity_evidence()
        self.assertEqual(evidence["recommendation"]["working_multiplier"], 1.3)
        self.assertEqual(
            {row["threshold_multiplier"] for row in evidence["latest_thresholds"]},
            {"1.20", "1.30", "1.40"},
        )
        self.assertEqual(evidence["significance_screen"]["latest_significant_report_count"], 145)
        self.assertFalse(evidence["privacy"]["manager_rates_persisted"])

    def test_loader_rejects_non_presentation_or_subthreshold_bucket(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "evidence.json"
            payload = json.loads(self.original_evidence.read_text(encoding="utf-8"))
            payload["deliverable_mode"] = "internal_analysis"
            path.write_text(json.dumps(payload), encoding="utf-8")
            DECK.ABOVE_AVERAGE_TEAM_TURNOVER_EVIDENCE = path
            with self.assertRaises(ValueError):
                DECK.above_average_team_turnover_evidence()

            payload = json.loads(self.original_evidence.read_text(encoding="utf-8"))
            payload["distribution"][0]["employee_count"] = 29
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                DECK.above_average_team_turnover_evidence()


if __name__ == "__main__":
    unittest.main()
