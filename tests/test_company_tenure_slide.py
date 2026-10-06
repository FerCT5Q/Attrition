"""Focused-refresh and stale-evidence tests for slide 27 Company tenure."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools" / "build_company_tenure_evidence.py"
DECK_PATH = ROOT / "tools" / "build_distribution_html_v2.py"

BUILDER_SPEC = importlib.util.spec_from_file_location("company_tenure_builder_slide_test", BUILDER_PATH)
assert BUILDER_SPEC is not None and BUILDER_SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(BUILDER)

DECK_SPEC = importlib.util.spec_from_file_location("company_tenure_deck_slide_test", DECK_PATH)
assert DECK_SPEC is not None and DECK_SPEC.loader is not None
DECK = importlib.util.module_from_spec(DECK_SPEC)
DECK_SPEC.loader.exec_module(DECK)


def audit_rows() -> list[dict[str, object]]:
    values = {
        "population_source_row_count": 200,
        "target_missing_employee_id_row_count": 0,
        "target_source_row_count": 200,
        "target_unique_employee_count": 200,
        "target_duplicate_employee_count": 0,
        "target_duplicate_row_excess_count": 0,
        "target_conflicting_employee_count": 0,
        "original_hire_null_count": 0,
        "latest_hire_rehire_null_count": 0,
        "original_hire_future_date_count": 0,
        "latest_hire_rehire_future_date_count": 0,
        "impossible_date_order_count": 0,
        "original_hire_calculable_employee_count": 200,
        "latest_hire_rehire_calculable_employee_count": 200,
    }
    return [
        {"snapshot_date": "2026-08-23", "row_type": "metric", "metric": key, "metric_value": value}
        for key, value in values.items()
    ]


def profile_rows() -> list[dict[str, object]]:
    original = [40, 35, 30, 35, 30, 30]
    latest = [35, 35, 30, 30, 35, 35]
    rows: list[dict[str, object]] = []
    for clock, counts in (("original_hire", original), ("latest_hire_rehire", latest)):
        rows.extend(
            [
                {"snapshot_date": "2026-08-23", "clock": clock, "row_type": "metric", "bucket_key": "calculable", "employee_count": 200},
                {"snapshot_date": "2026-08-23", "clock": clock, "row_type": "metric", "bucket_key": "not_calculable", "employee_count": 0},
            ]
        )
        rows.extend(
            {"snapshot_date": "2026-08-23", "clock": clock, "row_type": "band", "bucket_key": key, "employee_count": count}
            for key, count in zip(BUILDER.BAND_KEYS, counts)
        )
    return rows


def evidence() -> dict[str, object]:
    return BUILDER.build_evidence_from_rows(audit_rows(), profile_rows())


class CompanyTenureSlideTests(unittest.TestCase):
    def setUp(self):
        self.original_target = DECK.TARGET
        self.original_manifest = DECK.MANIFEST
        self.original_evidence = DECK.COMPANY_TENURE_EVIDENCE

    def tearDown(self):
        DECK.TARGET = self.original_target
        DECK.MANIFEST = self.original_manifest
        DECK.COMPANY_TENURE_EVIDENCE = self.original_evidence

    def test_loader_rejects_malformed_or_stale_evidence(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            path = Path(folder) / "evidence.json"
            payload = evidence()
            payload["snapshot_date"] = "2026-08-16"
            path.write_text(json.dumps(payload), encoding="utf-8")
            DECK.COMPANY_TENURE_EVIDENCE = path
            with self.assertRaisesRegex(ValueError, "publication contract"):
                DECK.company_tenure_distribution_evidence()

            payload = evidence()
            payload["provenance"]["profile_sql_sha256"] = "0" * 64
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stale"):
                DECK.company_tenure_distribution_evidence()

    def test_loader_rejects_a_visible_band_below_n30(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            path = Path(folder) / "evidence.json"
            payload = evidence()
            payload["distribution"][0]["original_hire_employee_count"] = 25
            path.write_text(json.dumps(payload), encoding="utf-8")
            DECK.COMPANY_TENURE_EVIDENCE = path
            with self.assertRaisesRegex(ValueError, "unsafe"):
                DECK.company_tenure_distribution_evidence()

    def test_slide_uses_two_field_proxies_and_keeps_not_calculable_in_right_card(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            path = Path(folder) / "evidence.json"
            path.write_text(json.dumps(evidence()), encoding="utf-8")
            DECK.COMPANY_TENURE_EVIDENCE = path
            frozen, original_data, latest_data = DECK.company_tenure_distribution_evidence()
            markup = DECK.company_tenure_slide(27, frozen)
            self.assertEqual([label for label, _ in original_data], [label for label, _ in latest_data])
            self.assertEqual(markup.count('class="card chart-card company-tenure-card"'), 2)
            self.assertIn("Service since original hire · field proxy", markup)
            self.assertIn("Service since latest hire / rehire · field proxy", markup)
            self.assertIn("Variables used in the two distributions", markup)
            self.assertIn("original_hire_date", markup)
            self.assertIn("max_hire_rehire_date", markup)
            self.assertEqual(markup.lower().count("not calculable"), 2)

    def test_focused_refresh_changes_only_stage_27_and_preserves_navigation(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            temp = Path(folder)
            target = temp / "deck.html"
            manifest = temp / "manifest.json"
            frozen = temp / "evidence.json"
            target.write_text(self.original_target.read_text(encoding="utf-8"), encoding="utf-8")
            manifest.write_text(self.original_manifest.read_text(encoding="utf-8"), encoding="utf-8")
            frozen.write_text(json.dumps(evidence(), ensure_ascii=False), encoding="utf-8")
            DECK.TARGET = target
            DECK.MANIFEST = manifest
            DECK.COMPANY_TENURE_EVIDENCE = frozen

            baseline = target.read_text(encoding="utf-8")
            baseline_hashes = DECK.slide_stage_hashes(baseline)
            baseline_nav = DECK.nav_pill_labels(baseline)
            DECK.refresh_company_tenure_slide()
            output = target.read_text(encoding="utf-8")
            new_hashes = DECK.slide_stage_hashes(output)
            new_nav = DECK.nav_pill_labels(output)
            changed_stages = [stage for stage in baseline_hashes if baseline_hashes[stage] != new_hashes[stage]]
            changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]

            self.assertEqual(changed_stages, ["slide-27"])
            self.assertEqual(changed_nav, [])
            self.assertEqual(new_nav[26], "27. Company tenure")
            self.assertIn("Service since original hire · field proxy", output)
            self.assertEqual(len(new_hashes), 46)
            self.assertEqual(len(new_nav), 46)
            refreshed_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(refreshed_manifest["slides"][26]["title"], "Company tenure")
            self.assertEqual(refreshed_manifest["slide_content_hash_validation"]["observed_changed_slides"], [27])
            self.assertEqual(refreshed_manifest["slide_content_hash_validation"]["observed_changed_navigation_labels"], [])
            self.assertNotIn(DECK.COMPANY_TENURE_LEGACY_PROFILE_SQL, refreshed_manifest["new_aggregate_profiles"])
            self.assertIn(DECK.COMPANY_TENURE_LEGACY_PROFILE_SQL, refreshed_manifest["historical_aggregate_profiles"])


if __name__ == "__main__":
    unittest.main()
