"""Focused-refresh and stale-evidence tests for slide 26."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools" / "build_role_level_tenure_evidence.py"
DECK_PATH = ROOT / "tools" / "build_distribution_html_v2.py"

BUILDER_SPEC = importlib.util.spec_from_file_location("role_level_builder_slide_test", BUILDER_PATH)
assert BUILDER_SPEC is not None and BUILDER_SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(BUILDER)

DECK_SPEC = importlib.util.spec_from_file_location("role_level_deck_slide_test", DECK_PATH)
assert DECK_SPEC is not None and DECK_SPEC.loader is not None
DECK = importlib.util.module_from_spec(DECK_SPEC)
DECK_SPEC.loader.exec_module(DECK)


def lineage() -> dict[str, object]:
    return {
        "artifact_type": "authoritative_lineage_confirmation",
        "authority": "HRIS data owner",
        "confirmation_date": "2026-09-10",
        "source_reference": "Approved HRIS data dictionary record",
        "time_in_job_profile_start_date_confirmed_construct": "current_job_profile_start",
        "job_level_primary_position_confirmed_construct": "current_detailed_level",
        "approved": True,
    }


def audit_rows() -> list[dict[str, object]]:
    values = {
        "target_source_row_count": 200, "target_unique_employee_count": 200,
        "target_duplicate_employee_count": 0, "target_duplicate_row_excess_count": 0,
        "target_conflicting_employee_count": 0, "role_start_future_date_count": 0,
        "level_start_future_date_count": 0, "rehire_date_future_count": 0,
        "rehire_flag_without_date_count": 0, "role_calculable_employee_count": 200,
        "level_calculable_employee_count": 200, "role_rehire_adjustment_count": 4,
        "level_rehire_adjustment_count": 3, "time_in_role_support_populated_count": 200,
        "history_duplicate_employee_snapshot_count": 0, "history_conflicting_employee_snapshot_count": 0,
        "comparable_transition_snapshot_count": 500, "detailed_level_transition_count": 40,
        "detailed_level_transition_with_date_reset_count": 40,
        "unexplained_detailed_level_transition_count": 0, "unexplained_detailed_level_reset_count": 0,
        "job_profile_start_reset_count": 50, "job_profile_reset_with_proxy_change_count": 45,
        "job_profile_reset_without_proxy_change_count": 5, "job_proxy_change_without_profile_reset_count": 60,
        "promotion_level_transition_intersection_count": 30, "demotion_level_transition_intersection_count": 2,
        "transfer_level_transition_intersection_count": 4, "rehire_level_transition_intersection_count": 1,
    }
    return [{"snapshot_date": "2026-08-23", "row_type": "metric", "metric": key, "metric_value": value} for key, value in values.items()]


def profile_rows() -> list[dict[str, object]]:
    role = [40, 35, 30, 35, 30, 30]
    level = [30, 40, 30, 30, 35, 35]
    rows: list[dict[str, object]] = []
    for clock, counts in (("role", role), ("level", level)):
        rows.extend([
            {"snapshot_date": "2026-08-23", "clock": clock, "row_type": "metric", "bucket_key": "calculable", "employee_count": 200},
            {"snapshot_date": "2026-08-23", "clock": clock, "row_type": "metric", "bucket_key": "not_calculable", "employee_count": 0},
        ])
        rows.extend(
            {"snapshot_date": "2026-08-23", "clock": clock, "row_type": "band", "bucket_key": key, "employee_count": count}
            for key, count in zip(BUILDER.BAND_KEYS, counts)
        )
    return rows


def evidence() -> dict[str, object]:
    return BUILDER.build_evidence_from_rows(lineage(), audit_rows(), profile_rows())


class RoleLevelTenureSlideTests(unittest.TestCase):
    def setUp(self):
        self.original_target = DECK.TARGET
        self.original_manifest = DECK.MANIFEST
        self.original_evidence = DECK.ROLE_LEVEL_TENURE_EVIDENCE

    def tearDown(self):
        DECK.TARGET = self.original_target
        DECK.MANIFEST = self.original_manifest
        DECK.ROLE_LEVEL_TENURE_EVIDENCE = self.original_evidence

    def test_loader_rejects_malformed_or_stale_evidence(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            path = Path(folder) / "evidence.json"
            payload = evidence()
            payload["snapshot_date"] = "2026-08-16"
            path.write_text(json.dumps(payload), encoding="utf-8")
            DECK.ROLE_LEVEL_TENURE_EVIDENCE = path
            with self.assertRaisesRegex(ValueError, "publication contract"):
                DECK.role_level_tenure_distribution_evidence()

            payload = evidence()
            payload["provenance"]["audit_sql_sha256"] = "0" * 64
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stale"):
                DECK.role_level_tenure_distribution_evidence()

    def test_loader_rejects_a_published_band_below_n30(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            path = Path(folder) / "evidence.json"
            payload = evidence()
            payload["distribution"][0]["role_employee_count"] = 25
            path.write_text(json.dumps(payload), encoding="utf-8")
            DECK.ROLE_LEVEL_TENURE_EVIDENCE = path
            with self.assertRaisesRegex(ValueError, "unsafe band"):
                DECK.role_level_tenure_distribution_evidence()

    def test_slide_has_two_shared_band_cards_and_keeps_unavailable_counts_in_evidence_panel(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            path = Path(folder) / "evidence.json"
            path.write_text(json.dumps(evidence()), encoding="utf-8")
            DECK.ROLE_LEVEL_TENURE_EVIDENCE = path
            frozen, role_data, level_data = DECK.role_level_tenure_distribution_evidence()
            markup = DECK.role_level_tenure_slide(26, frozen)
            self.assertEqual([label for label, _ in role_data], [label for label, _ in level_data])
            self.assertEqual(markup.count('class="card chart-card role-level-tenure-card"'), 2)
            self.assertIn("Time in current job profile", markup)
            self.assertIn("Time at current detailed level", markup)
            self.assertEqual(markup.lower().count("not calculable"), 2)

    def test_loader_accepts_caveated_exploratory_evidence_and_lists_the_input_fields(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as folder:
            path = Path(folder) / "evidence.json"
            exploratory = BUILDER.build_evidence_from_rows(
                None,
                [
                    {**row, "metric_value": 6}
                    if row["metric"] == "unexplained_detailed_level_transition_count"
                    else row
                    for row in audit_rows()
                ],
                profile_rows(),
                exploratory=True,
            )
            path.write_text(json.dumps(exploratory), encoding="utf-8")
            DECK.ROLE_LEVEL_TENURE_EVIDENCE = path
            frozen, _, _ = DECK.role_level_tenure_distribution_evidence()
            markup = DECK.role_level_tenure_slide(26, frozen)
            self.assertEqual(frozen["publication_status"], "exploratory")
            self.assertIn("time_in_job_profile_start_date + max_hire_rehire_date", markup)
            self.assertIn("levelentrydate + job_level_primary_position + max_hire_rehire_date", markup)
            self.assertIn("Variables used in the two distributions", markup)

    def test_focused_refresh_changes_only_stage_26_and_its_navigation_label(self):
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
            DECK.ROLE_LEVEL_TENURE_EVIDENCE = frozen

            # Seed the legacy navigation label so this test verifies both
            # permitted focused changes even after the checked-in deck has
            # already been refreshed once.
            seeded = target.read_text(encoding="utf-8").replace(
                '26. Time in role and level</button>',
                '26. Time in level</button>',
                1,
            )
            target.write_text(seeded, encoding="utf-8")
            baseline = seeded
            baseline_hashes = DECK.slide_stage_hashes(baseline)
            baseline_nav = DECK.nav_pill_labels(baseline)
            DECK.refresh_role_level_tenure_slide()
            output = target.read_text(encoding="utf-8")
            new_hashes = DECK.slide_stage_hashes(output)
            new_nav = DECK.nav_pill_labels(output)
            changed_stages = [stage for stage in baseline_hashes if baseline_hashes[stage] != new_hashes[stage]]
            changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]

            self.assertEqual(changed_stages, ["slide-26"])
            self.assertEqual(changed_nav, [25])
            self.assertEqual(new_nav[25], "26. Time in role and level")
            self.assertIn("Time in current job profile vs. current detailed level", output)
            self.assertEqual(len(new_hashes), 46)
            self.assertEqual(len(new_nav), 46)
            refreshed_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(refreshed_manifest["slides"][25]["title"], "Time in role and level")
            self.assertEqual(refreshed_manifest["slide_content_hash_validation"]["observed_changed_slides"], [26])


if __name__ == "__main__":
    unittest.main()
