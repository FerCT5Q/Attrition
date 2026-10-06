"""Offline publication-gate tests for the role/profile versus detailed-level slide."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_role_level_tenure_evidence.py"
SPEC = importlib.util.spec_from_file_location("role_level_tenure_builder_test", BUILDER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


BASE_AUDIT = {
    "target_source_row_count": 200,
    "target_unique_employee_count": 200,
    "target_duplicate_employee_count": 0,
    "target_duplicate_row_excess_count": 0,
    "target_conflicting_employee_count": 0,
    "role_start_future_date_count": 0,
    "level_start_future_date_count": 0,
    "rehire_date_future_count": 0,
    "rehire_flag_without_date_count": 0,
    "role_calculable_employee_count": 200,
    "level_calculable_employee_count": 200,
    "role_rehire_adjustment_count": 4,
    "level_rehire_adjustment_count": 3,
    "time_in_role_support_populated_count": 200,
    "history_duplicate_employee_snapshot_count": 0,
    "history_conflicting_employee_snapshot_count": 0,
    "comparable_transition_snapshot_count": 500,
    "detailed_level_transition_count": 40,
    "detailed_level_transition_with_date_reset_count": 40,
    "unexplained_detailed_level_transition_count": 0,
    "unexplained_detailed_level_reset_count": 0,
    "job_profile_start_reset_count": 50,
    "job_profile_reset_with_proxy_change_count": 45,
    "job_profile_reset_without_proxy_change_count": 5,
    "job_proxy_change_without_profile_reset_count": 60,
    "promotion_level_transition_intersection_count": 30,
    "demotion_level_transition_intersection_count": 2,
    "transfer_level_transition_intersection_count": 4,
    "rehire_level_transition_intersection_count": 1,
}
ROLE_COUNTS = [40, 35, 30, 35, 30, 30]
LEVEL_COUNTS = [30, 40, 30, 30, 35, 35]


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


def audit_rows(overrides: dict[str, int] | None = None, snapshot: str = "2026-08-23") -> list[dict[str, object]]:
    values = {**BASE_AUDIT, **(overrides or {})}
    return [
        {"snapshot_date": snapshot, "row_type": "metric", "metric": metric, "metric_value": value}
        for metric, value in values.items()
    ]


def profile_rows(
    role_counts: list[int] | None = None,
    level_counts: list[int] | None = None,
    *,
    role_not_calculable: int = 0,
    level_not_calculable: int = 0,
    snapshot: str = "2026-08-23",
) -> list[dict[str, object]]:
    role_counts = role_counts or ROLE_COUNTS
    level_counts = level_counts or LEVEL_COUNTS
    rows: list[dict[str, object]] = []
    for clock, counts, unavailable in (("role", role_counts, role_not_calculable), ("level", level_counts, level_not_calculable)):
        rows.extend(
            [
                {"snapshot_date": snapshot, "clock": clock, "row_type": "metric", "bucket_key": "calculable", "employee_count": sum(counts)},
                {"snapshot_date": snapshot, "clock": clock, "row_type": "metric", "bucket_key": "not_calculable", "employee_count": unavailable},
            ]
        )
        rows.extend(
            {
                "snapshot_date": snapshot,
                "clock": clock,
                "row_type": "band",
                "bucket_key": key,
                "employee_count": count,
            }
            for key, count in zip(MODULE.BAND_KEYS, counts)
        )
    return rows


class RoleLevelTenureEvidenceGateTests(unittest.TestCase):
    def build(self, audit_overrides: dict[str, int] | None = None, **profile_kwargs):
        return MODULE.build_evidence_from_rows(lineage(), audit_rows(audit_overrides), profile_rows(**profile_kwargs))

    def test_builds_shared_ordered_bands_with_exact_totals(self):
        evidence = self.build()
        distribution = evidence["distribution"]
        self.assertEqual([row["source_band_keys"] for row in distribution], [[key] for key in MODULE.BAND_KEYS])
        self.assertEqual(sum(row["role_employee_count"] for row in distribution), 200)
        self.assertEqual(sum(row["level_employee_count"] for row in distribution), 200)
        self.assertAlmostEqual(sum(row["role_percent_of_calculable"] for row in distribution), 100.0)
        self.assertAlmostEqual(sum(row["level_percent_of_calculable"] for row in distribution), 100.0)
        self.assertTrue(all(row["role_employee_count"] >= 30 and row["level_employee_count"] >= 30 for row in distribution))

    def test_pools_adjacent_bands_identically_when_one_clock_is_sparse(self):
        role = [10, 65, 30, 35, 30, 30]
        level = [20, 50, 30, 30, 35, 35]
        evidence = MODULE.build_evidence_from_rows(
            lineage(),
            audit_rows({"role_calculable_employee_count": sum(role), "level_calculable_employee_count": sum(level), "target_source_row_count": sum(role), "target_unique_employee_count": sum(role), "time_in_role_support_populated_count": sum(role)}),
            profile_rows(role, level),
        )
        first = evidence["distribution"][0]
        self.assertEqual(first["source_band_keys"], ["lt_1", "y1_to_lt2"])
        self.assertGreaterEqual(first["role_employee_count"], 30)
        self.assertGreaterEqual(first["level_employee_count"], 30)

    def test_rejects_snapshot_mismatch(self):
        with self.assertRaisesRegex(ValueError, "Snapshot mismatch"):
            MODULE.build_evidence_from_rows(lineage(), audit_rows(snapshot="2026-08-16"), profile_rows())

    def test_rejects_duplicate_or_conflicting_input(self):
        with self.assertRaisesRegex(ValueError, "target_duplicate_employee_count"):
            self.build({"target_duplicate_employee_count": 1})
        with self.assertRaisesRegex(ValueError, "target_conflicting_employee_count"):
            self.build({"target_conflicting_employee_count": 1})

    def test_rejects_future_dates_and_unresolved_rehire_conflict(self):
        with self.assertRaisesRegex(ValueError, "role_start_future_date_count"):
            self.build({"role_start_future_date_count": 1})
        with self.assertRaisesRegex(ValueError, "rehire_flag_without_date_count"):
            self.build({"rehire_flag_without_date_count": 1})

    def test_rejects_unexplained_detailed_level_reset(self):
        with self.assertRaisesRegex(ValueError, "unexplained_detailed_level_reset_count"):
            self.build({"unexplained_detailed_level_reset_count": 1})

    def test_exploratory_mode_keeps_transition_gap_as_a_visible_warning(self):
        evidence = MODULE.build_evidence_from_rows(
            None,
            audit_rows({"unexplained_detailed_level_transition_count": 6, "unexplained_detailed_level_reset_count": 2}),
            profile_rows(),
            exploratory=True,
        )
        self.assertEqual(evidence["publication_status"], "exploratory")
        self.assertEqual(evidence["authoritative_lineage"]["status"], "not_confirmed")
        self.assertEqual(evidence["validations"]["detailed_level_transition"]["outcome"], "warning")

    def test_rejects_unreconciled_profile_totals(self):
        broken = profile_rows()
        for row in broken:
            if row["clock"] == "role" and row["row_type"] == "band" and row["bucket_key"] == "lt_1":
                row["employee_count"] = 41
        with self.assertRaisesRegex(ValueError, "bands do not reconcile"):
            MODULE.build_evidence_from_rows(lineage(), audit_rows(), broken)

    def test_rejects_calculable_population_below_privacy_threshold(self):
        low = [3, 3, 3, 3, 4, 4]
        with self.assertRaisesRegex(ValueError, "minimum publication cohort"):
            MODULE.build_evidence_from_rows(
                lineage(),
                audit_rows({
                    "target_source_row_count": 20,
                    "target_unique_employee_count": 20,
                    "role_calculable_employee_count": 20,
                    "level_calculable_employee_count": 20,
                    "time_in_role_support_populated_count": 20,
                }),
                profile_rows(low, low),
            )

    def test_rejects_missing_lineage_and_prohibited_persisted_keys(self):
        incomplete = lineage()
        incomplete["approved"] = False
        with self.assertRaisesRegex(ValueError, "not approved"):
            MODULE.build_evidence_from_rows(incomplete, audit_rows(), profile_rows())
        with self.assertRaisesRegex(ValueError, "prohibited key"):
            MODULE.ensure_no_sensitive_keys({"employee_id": 99})


if __name__ == "__main__":
    unittest.main()
