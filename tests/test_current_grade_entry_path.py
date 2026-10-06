"""Offline gates for the current-compensation-grade entry-path evidence and slide."""

from __future__ import annotations

import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = load_module("current_grade_entry_builder_test", ROOT / "tools" / "build_current_grade_entry_path_evidence.py")
DECK = load_module("current_grade_entry_deck_test", ROOT / "tools" / "build_distribution_html_v2.py")


class CurrentGradeEntryPathTests(unittest.TestCase):
    def test_builder_reconciles_and_rounds_each_grade(self):
        audit, profile = BUILDER.synthetic_rows()
        evidence = BUILDER.build_evidence_from_rows(audit, profile, execution_date="2026-09-10")
        self.assertEqual(len(evidence["matrix"]), 3)
        self.assertTrue(all(round(sum(row[f"{key}_percent"] for key in BUILDER.CATEGORY_KEYS), 1) == 100.0 for row in evidence["matrix"]))
        self.assertEqual(sum(row["total_employee_count"] for row in evidence["matrix"]), 630)

    def test_builder_rejects_old_grade_as_a_reconciled_definition_and_private_key(self):
        audit, profile = BUILDER.synthetic_rows()
        altered = deepcopy(audit)
        next(row for row in altered if row["metric"] == "old_grade_mismatch_previous_snapshot_count")["metric_value"] = 0
        next(row for row in altered if row["metric"] == "old_grade_matches_previous_snapshot_count")["metric_value"] = 4100
        with self.assertRaises(ValueError):
            BUILDER.build_evidence_from_rows(altered, profile)
        with self.assertRaises(ValueError):
            BUILDER.ensure_no_sensitive_keys({"employee_id": 1})

    def test_saved_sql_selects_latest_observed_entry_and_profile_does_not_use_old_grade(self):
        audit_sql = (ROOT / "queries" / "audits" / "current_grade_entry_path_integrity_20260823.sql").read_text(encoding="utf-8")
        profile_sql = (ROOT / "queries" / "profiles" / "current_grade_entry_path_20260823.sql").read_text(encoding="utf-8")
        self.assertIn("ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY snapshot_date DESC)", audit_sql)
        self.assertIn("promotion_date > entry.previous_snapshot_date", audit_sql)
        self.assertIn("promotion_date <= entry.entry_snapshot_date", audit_sql)
        self.assertIn("compensation_grade_old", audit_sql)
        self.assertNotIn("compensation_grade_old", profile_sql)

    def test_deck_contract_has_two_panels_and_46_slide_inventory(self):
        evidence, matrix = DECK.current_grade_entry_path_evidence()
        markup = DECK.current_grade_entry_path_slide(30, evidence)
        self.assertEqual(len(matrix), 16)
        self.assertEqual(markup.count("entry-path-card"), 2)
        self.assertEqual(markup.count("entry-path-read-guide"), 1)
        self.assertIn("Internal exploratory analysis", markup)
        self.assertIn("direct hire", markup)
        self.assertIn("Blue · Recorded promotion", markup)
        self.assertIn("Green · Grade change observed", markup)
        self.assertIn("Brown · Entry not observable", markup)
        document = DECK.TARGET.read_text(encoding="utf-8")
        self.assertEqual(len(DECK.slide_stage_hashes(document)), 46)
        self.assertEqual(len(DECK.nav_pill_labels(document)), 46)
        manifest = json.loads(DECK.MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["slides"][29]["title"], "Current grade entry path")


if __name__ == "__main__":
    unittest.main()
