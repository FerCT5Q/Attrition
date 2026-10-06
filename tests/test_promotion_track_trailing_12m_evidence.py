import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.promotion-track-trailing-12m-evidence-20260918.json"


class PromotionTrackEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_fixed_august_window_and_pass(self):
        self.assertEqual(self.evidence["outcome"], "pass")
        self.assertEqual(self.evidence["window"]["snapshot_date"], "2026-08-23")
        self.assertEqual(self.evidence["window"]["start_exclusive"], "2025-08-24")
        self.assertEqual(self.evidence["window"]["monthly_snapshot_count"], 12)

    def test_display_rows_reconcile_and_are_safe(self):
        rows = self.evidence["display_rows"]
        self.assertEqual([row["track"] for row in rows], ["R", "T", "P", "M", "S", "V"])
        self.assertTrue(all(row["current_employee_count"] >= 30 for row in rows))
        self.assertAlmostEqual(
            sum(row["current_employee_count"] for row in rows)
            / self.evidence["totals"]["current_employee_count"]
            * 100,
            self.evidence["privacy"]["visible_distribution_coverage_percent"],
            places=8,
        )
        serialized = json.dumps(self.evidence, ensure_ascii=False).lower()
        for forbidden in ('"employee_id"', '"employee_key"', '"email"', '"salary"'):
            self.assertNotIn(forbidden, serialized)

    def test_rate_reconciliation_and_exit_coverage(self):
        self.assertGreaterEqual(self.evidence["exit_track_assignment"]["coverage_percent"], 99.5)
        self.assertEqual(self.evidence["totals"]["assigned_voluntary_exit_count"], 2603)
        for row in self.evidence["display_rows"]:
            self.assertAlmostEqual(
                row["promotion_rate_percent"],
                100 * row["promoted_employee_count"] / row["promotion_participant_count"],
                places=4,
            )
            self.assertAlmostEqual(
                row["attrition_rate_percent"],
                100 * row["voluntary_exit_count"] / row["average_monthly_headcount"],
                places=4,
            )


if __name__ == "__main__":
    unittest.main()
