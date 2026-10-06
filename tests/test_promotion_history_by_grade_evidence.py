"""Offline publication-gate tests for promotion history by current grade."""

from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools" / "build_promotion_history_by_compensation_grade_evidence.py"
SPEC = importlib.util.spec_from_file_location("promotion_history_grade_builder_test", BUILDER_PATH)
assert SPEC is not None and SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class PromotionHistoryByGradeEvidenceTests(unittest.TestCase):
    def build(self, audit_rows=None, profile_rows=None):
        audit, profile = BUILDER.synthetic_rows()
        return BUILDER.build_evidence_from_rows(audit_rows or audit, profile_rows or profile)

    def test_builds_14_reconciled_rows_and_dynamic_other_pool(self):
        evidence = self.build()
        matrix = evidence["matrix"]
        self.assertEqual(len(matrix), 14)
        self.assertEqual(sum(row["total_employee_count"] for row in matrix), 2105)
        self.assertEqual(matrix[-1]["grade"], "Other grades")
        self.assertEqual(evidence["metrics"]["individual_grade_count"], 13)
        self.assertEqual(evidence["metrics"]["pooled_other_grade_count"], 2)
        self.assertTrue(all(row[key] >= 30 for row in matrix for key in BUILDER.CATEGORY_KEYS))
        self.assertTrue(all(round(sum(row[f"{key}_percent"] for key in BUILDER.CATEGORY_KEYS), 1) == 100.0 for row in matrix))

    def test_rejects_wrong_snapshot_and_integrity_failures(self):
        audit, profile = BUILDER.synthetic_rows()
        profile[0]["snapshot_date"] = "2026-08-24"
        with self.assertRaisesRegex(ValueError, "Snapshot mismatch"):
            BUILDER.build_evidence_from_rows(audit, profile)

        for metric in (
            "target_duplicate_employee_count",
            "target_conflicting_grade_count",
            "invalid_promo_flag_count",
            "future_promotion_date_count",
            "selected_event_before_current_episode_count",
        ):
            audit, profile = BUILDER.synthetic_rows()
            BUILDER.replace_audit_metric(audit, metric, 1)
            with self.assertRaisesRegex(ValueError, "nonzero safeguards"):
                BUILDER.build_evidence_from_rows(audit, profile)

    def test_rejects_category_reconciliation_and_partial_history_gaps(self):
        audit, profile = BUILDER.synthetic_rows()
        row = next(item for item in profile if item["category_key"] == "observable_history_employee_count")
        row["employee_count"] = int(row["employee_count"]) - 1
        with self.assertRaisesRegex(ValueError, "0/1/2\\+ categories"):
            BUILDER.build_evidence_from_rows(audit, profile)

        audit, profile = BUILDER.synthetic_rows()
        row = next(item for item in profile if item["category_key"] == "partial_history_employee_count")
        row["employee_count"] = int(row["employee_count"]) - 1
        with self.assertRaisesRegex(ValueError, "Partial promotion history"):
            BUILDER.build_evidence_from_rows(audit, profile)

    def test_rejects_a_visible_cell_below_n30_and_bad_other_pool(self):
        audit, profile = BUILDER.synthetic_rows()
        row = next(
            item for item in profile
            if item["row_type"] == "grade_category"
            and item["compensation_grade"] == "G01"
            and item["category_key"] == "zero_recorded_promotions"
        )
        row["employee_count"] = 29
        with self.assertRaisesRegex(ValueError, "Grade-category totals|published compensation-grade cell"):
            BUILDER.build_evidence_from_rows(audit, profile)

        audit, profile = BUILDER.synthetic_rows()
        for grade in ("S1", "S2"):
            row = next(
                item for item in profile
                if item["row_type"] == "grade_category"
                and item["compensation_grade"] == grade
                and item["category_key"] == "zero_recorded_promotions"
            )
            row["employee_count"] = 10
        with self.assertRaisesRegex(ValueError, "Grade-category totals|Other grades"):
            BUILDER.build_evidence_from_rows(audit, profile)

    def test_rejects_sensitive_persisted_keys(self):
        with self.assertRaisesRegex(ValueError, "prohibited key"):
            BUILDER.ensure_no_sensitive_keys({"employee_id": 7})
        with self.assertRaisesRegex(ValueError, "prohibited key"):
            BUILDER.ensure_no_sensitive_keys({"raw_rows": []})


if __name__ == "__main__":
    unittest.main()
