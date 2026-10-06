"""Focused-refresh and stale-evidence tests for the new slide 29 matrix."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECK_PATH = ROOT / "tools" / "build_distribution_html_v2.py"
SPEC = importlib.util.spec_from_file_location("promotion_history_grade_deck_test", DECK_PATH)
assert SPEC is not None and SPEC.loader is not None
DECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DECK)


class PromotionHistoryByGradeSlideTests(unittest.TestCase):
    def setUp(self):
        self.original_target = DECK.TARGET
        self.original_manifest = DECK.MANIFEST
        self.original_evidence = DECK.PROMOTION_HISTORY_BY_GRADE_EVIDENCE

    def tearDown(self):
        DECK.TARGET = self.original_target
        DECK.MANIFEST = self.original_manifest
        DECK.PROMOTION_HISTORY_BY_GRADE_EVIDENCE = self.original_evidence

    def frozen_evidence(self) -> dict[str, object]:
        return json.loads(self.original_evidence.read_text(encoding="utf-8"))

    def test_loader_rejects_stale_malformed_or_sensitive_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "evidence.json"
            payload = self.frozen_evidence()
            payload["snapshot_date"] = "2026-08-16"
            path.write_text(json.dumps(payload), encoding="utf-8")
            DECK.PROMOTION_HISTORY_BY_GRADE_EVIDENCE = path
            with self.assertRaisesRegex(ValueError, "publication contract"):
                DECK.promotion_history_by_grade_evidence()

            payload = self.frozen_evidence()
            payload["provenance"]["profile_sql_sha256"] = "0" * 64
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stale"):
                DECK.promotion_history_by_grade_evidence()

            payload = self.frozen_evidence()
            payload["employee_id"] = "forbidden"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "restricted"):
                DECK.promotion_history_by_grade_evidence()

    def test_loader_rejects_visible_cell_below_n30(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "evidence.json"
            payload = self.frozen_evidence()
            payload["matrix"][0]["zero_recorded_promotions"] = 29
            path.write_text(json.dumps(payload), encoding="utf-8")
            DECK.PROMOTION_HISTORY_BY_GRADE_EVIDENCE = path
            with self.assertRaisesRegex(ValueError, "below n=30"):
                DECK.promotion_history_by_grade_evidence()

    def test_slide_renders_two_seven_row_count_matrices(self):
        evidence, matrix = DECK.promotion_history_by_grade_evidence()
        markup = DECK.promotion_history_by_grade_slide(29, evidence)
        self.assertEqual(len(matrix), 14)
        self.assertEqual(markup.count('promotion-grade-matrix-card'), 2)
        self.assertEqual(markup.count('<tbody>'), 2)
        self.assertIn("Partial promotion", markup)
        self.assertIn("Internal exploratory analysis", markup)
        self.assertIn("not a causal attrition finding", markup)

    def test_focused_refresh_changes_only_slide_29_and_its_navigation_label(self):
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder)
            target = temp / "deck.html"
            manifest = temp / "manifest.json"
            baseline = self.original_target.read_text(encoding="utf-8")
            stage_id, start, end, _ = DECK.slide_stage_by_title(
                baseline,
                "Promotion history by current compensation grade",
            )
            self.assertEqual(stage_id, "slide-29")
            legacy_stage = DECK.support_slide(
                29,
                "Promoted vs. hired into level",
                "Legacy support slide",
                "Legacy promotion-path placeholder",
                "The focused refresh must replace this stage from frozen aggregate evidence.",
                [("Status", "legacy baseline")],
            )
            baseline = baseline[:start] + legacy_stage + "\n\n  " + baseline[end:]
            baseline = baseline.replace(
                '<button class="nav-pill" data-slide="28">29. Promotions by grade</button>',
                '<button class="nav-pill" data-slide="28">29. Promoted vs hired</button>',
                1,
            )
            target.write_text(baseline, encoding="utf-8")
            manifest.write_text(self.original_manifest.read_text(encoding="utf-8"), encoding="utf-8")
            DECK.TARGET = target
            DECK.MANIFEST = manifest

            baseline = target.read_text(encoding="utf-8")
            baseline_hashes = DECK.slide_stage_hashes(baseline)
            baseline_nav = DECK.nav_pill_labels(baseline)
            DECK.refresh_promotion_history_by_grade_slide()
            output = target.read_text(encoding="utf-8")
            new_hashes = DECK.slide_stage_hashes(output)
            new_nav = DECK.nav_pill_labels(output)
            changed_stages = [stage for stage in baseline_hashes if baseline_hashes[stage] != new_hashes[stage]]
            changed_nav = [index for index, values in enumerate(zip(baseline_nav, new_nav)) if values[0] != values[1]]

            self.assertEqual(changed_stages, ["slide-29"])
            self.assertEqual(changed_nav, [28])
            self.assertEqual(new_nav[28], "29. Promotions by grade")
            self.assertIn("Promotion history by current compensation grade", output)
            self.assertEqual(len(new_hashes), 46)
            self.assertEqual(len(new_nav), 46)
            refreshed_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(refreshed_manifest["slides"][28]["title"], "Promotion history by current compensation grade")
            self.assertEqual(refreshed_manifest["slide_content_hash_validation"]["observed_changed_slides"], [29])
            self.assertEqual(refreshed_manifest["slide_content_hash_validation"]["observed_changed_navigation_labels"], [28])


if __name__ == "__main__":
    unittest.main()
