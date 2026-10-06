"""Regression checks for the authorized internal V7 promotion-cohort slide."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.time-since-last-promotion-comparable-cohorts-evidence-20260924.json"
DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"
MANIFEST = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7-manifest.json"


def slide(deck: str, stage_id: int) -> str:
    match = re.search(
        rf'<div class="slide-stage" id="slide-{stage_id}".*?(?=\n\s*<div class="slide-stage"|\n\s*<script|\Z)',
        deck,
        flags=re.S,
    )
    if match is None:
        raise AssertionError(f"Missing slide-{stage_id}.")
    return match.group(0)


class ComparablePromotionCohortSlideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.deck = DECK.read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.stage = slide(cls.deck, 32)

    def test_contract_is_fixed_baseline_internal_evidence(self) -> None:
        self.assertEqual(self.evidence["artifact_classification"], "internal_analysis")
        self.assertEqual(self.evidence["deliverable_mode"], "internal_analysis")
        self.assertTrue(self.evidence["authorization"]["small_cell_exception_applied"])
        self.assertEqual(self.evidence["outcome_contract"]["baseline_snapshot_date"], "2025-08-24")
        self.assertEqual(self.evidence["outcome_contract"]["outcome_window"], "(2025-08-24, 2026-08-23]")
        self.assertEqual(self.evidence["validation"]["rf360_exclusion_applied"], "pass")
        totals = self.evidence["cohort_totals"]
        self.assertEqual(
            totals["baseline_population"],
            totals["recorded_promotion"] + totals["no_recorded_promotion_role_tenure_proxy"] + totals["declared_exclusions"],
        )

    def test_authorized_small_band_exposes_descriptive_aggregate_values(self) -> None:
        for panel in (
            self.evidence["recorded_promotion_distribution"],
            self.evidence["no_recorded_promotion_role_tenure_proxy_distribution"],
        ):
            self.assertEqual(len(panel), 5)
            for row in panel:
                if row["publication_status"] == "publishable":
                    self.assertGreaterEqual(row["employee_count"], 30)
                    self.assertIn("annual_attrition_rate_percent", row)
                else:
                    self.assertEqual(row["publication_status"], "internal_exploratory_small_cohort")
                    self.assertLess(row["employee_count"], 30)
                    self.assertIn("annual_attrition_rate_percent", row)
                    self.assertIn("display_note", row)
        five_plus = self.evidence["recorded_promotion_distribution"][-1]
        self.assertEqual(five_plus["label"], "5+ years")
        self.assertEqual(five_plus["employee_count"], 7)
        self.assertEqual(five_plus["voluntary_exits"], 0)
        self.assertEqual(five_plus["annual_attrition_rate_percent"], 0.0)

    def test_slide_replaces_the_old_non_temporal_panel(self) -> None:
        self.assertIn('data-v7-promotion-comparable-cohorts="true"', self.stage)
        self.assertIn("Time since latest recorded promotion", self.stage)
        self.assertIn("People with no recorded promotion", self.stage)
        self.assertIn("not “never promoted”", self.stage)
        self.assertIn("excluding RF360", self.stage)
        self.assertIn("n=7", self.stage)
        self.assertIn(">0.0%*</span>", self.stage)
        self.assertIn("internal-small-cohort", self.stage)
        self.assertNotIn("Non-temporal observed-history states", self.stage)
        self.assertEqual(self.stage.count("v7-promotion-comparable-row"), 10)
        for forbidden in ("employee_id", "manager_employee_id", "manager_name", "term_date", "promotion_date"):
            self.assertNotIn(forbidden, self.stage.lower())

    def test_manifest_tracks_the_new_evidence(self) -> None:
        entry = self.manifest["updated_slides_27_39"]["promotion_evidence"]
        self.assertEqual(entry["path"], str(EVIDENCE.relative_to(ROOT)).replace("\\", "/"))
        self.assertEqual(entry["sha256"], hashlib.sha256(EVIDENCE.read_bytes()).hexdigest())
        self.assertEqual(entry["deliverable_mode"], "internal_analysis")
        self.assertEqual(entry["small_cohort_display"], [{"cohort": "recorded_promotion", "label": "5+ years", "employee_count": 7}])


if __name__ == "__main__":
    unittest.main()
