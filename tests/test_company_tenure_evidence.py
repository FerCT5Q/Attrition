"""Offline publication-gate tests for the Company tenure field-proxy evidence."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_company_tenure_evidence.py"
SPEC = importlib.util.spec_from_file_location("company_tenure_builder_test", BUILDER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


ORIGINAL_COUNTS = [40, 35, 30, 35, 30, 30]
LATEST_COUNTS = [35, 35, 30, 30, 35, 35]


def audit_rows(
    overrides: dict[str, int] | None = None,
    *,
    eligible: int = 200,
    original_calculable: int = 200,
    latest_calculable: int = 200,
    snapshot: str = "2026-08-23",
) -> list[dict[str, object]]:
    values = {
        "population_source_row_count": eligible,
        "target_missing_employee_id_row_count": 0,
        "target_source_row_count": eligible,
        "target_unique_employee_count": eligible,
        "target_duplicate_employee_count": 0,
        "target_duplicate_row_excess_count": 0,
        "target_conflicting_employee_count": 0,
        "original_hire_null_count": eligible - original_calculable,
        "latest_hire_rehire_null_count": eligible - latest_calculable,
        "original_hire_future_date_count": 0,
        "latest_hire_rehire_future_date_count": 0,
        "impossible_date_order_count": 0,
        "original_hire_calculable_employee_count": original_calculable,
        "latest_hire_rehire_calculable_employee_count": latest_calculable,
    }
    values.update(overrides or {})
    return [
        {"snapshot_date": snapshot, "row_type": "metric", "metric": key, "metric_value": value}
        for key, value in values.items()
    ]


def profile_rows(
    original_counts: list[int] | None = None,
    latest_counts: list[int] | None = None,
    *,
    original_not_calculable: int = 0,
    latest_not_calculable: int = 0,
    snapshot: str = "2026-08-23",
) -> list[dict[str, object]]:
    original_counts = original_counts or ORIGINAL_COUNTS
    latest_counts = latest_counts or LATEST_COUNTS
    rows: list[dict[str, object]] = []
    for clock, counts, unavailable in (
        ("original_hire", original_counts, original_not_calculable),
        ("latest_hire_rehire", latest_counts, latest_not_calculable),
    ):
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


class CompanyTenureEvidenceGateTests(unittest.TestCase):
    def build(self, audit_overrides: dict[str, int] | None = None, **profile_kwargs):
        profiles = profile_rows(**profile_kwargs)
        original_calculable = next(
            int(row["employee_count"])
            for row in profiles
            if row["clock"] == "original_hire" and row["row_type"] == "metric" and row["bucket_key"] == "calculable"
        )
        latest_calculable = next(
            int(row["employee_count"])
            for row in profiles
            if row["clock"] == "latest_hire_rehire" and row["row_type"] == "metric" and row["bucket_key"] == "calculable"
        )
        original_unavailable = next(
            int(row["employee_count"])
            for row in profiles
            if row["clock"] == "original_hire" and row["row_type"] == "metric" and row["bucket_key"] == "not_calculable"
        )
        latest_unavailable = next(
            int(row["employee_count"])
            for row in profiles
            if row["clock"] == "latest_hire_rehire" and row["row_type"] == "metric" and row["bucket_key"] == "not_calculable"
        )
        eligible = original_calculable + original_unavailable
        self.assertEqual(eligible, latest_calculable + latest_unavailable)
        return MODULE.build_evidence_from_rows(
            audit_rows(
                audit_overrides,
                eligible=eligible,
                original_calculable=original_calculable,
                latest_calculable=latest_calculable,
            ),
            profiles,
        )

    def test_builds_exact_shared_bands_and_reconciled_percentages(self):
        evidence = self.build()
        distribution = evidence["distribution"]
        self.assertEqual([row["source_band_key"] for row in distribution], list(MODULE.BAND_KEYS))
        self.assertEqual(sum(row["original_hire_employee_count"] for row in distribution), 200)
        self.assertEqual(sum(row["latest_hire_rehire_employee_count"] for row in distribution), 200)
        self.assertAlmostEqual(sum(row["original_hire_percent_of_calculable"] for row in distribution), 100.0)
        self.assertAlmostEqual(sum(row["latest_hire_rehire_percent_of_calculable"] for row in distribution), 100.0)
        self.assertTrue(all(row["original_hire_employee_count"] >= 30 and row["latest_hire_rehire_employee_count"] >= 30 for row in distribution))

    def test_rejects_wrong_snapshot(self):
        with self.assertRaisesRegex(ValueError, "Snapshot mismatch"):
            MODULE.build_evidence_from_rows(audit_rows(snapshot="2026-08-16"), profile_rows())

    def test_rejects_duplicate_or_conflicting_employee_snapshot_rows(self):
        with self.assertRaisesRegex(ValueError, "target_duplicate_employee_count"):
            self.build({"target_duplicate_employee_count": 1})
        with self.assertRaisesRegex(ValueError, "target_conflicting_employee_count"):
            self.build({"target_conflicting_employee_count": 1})

    def test_rejects_future_dates_and_impossible_order(self):
        with self.assertRaisesRegex(ValueError, "original_hire_future_date_count"):
            self.build({"original_hire_future_date_count": 1})
        with self.assertRaisesRegex(ValueError, "latest_hire_rehire_future_date_count"):
            self.build({"latest_hire_rehire_future_date_count": 1})
        with self.assertRaisesRegex(ValueError, "impossible_date_order_count"):
            self.build({"impossible_date_order_count": 1})

    def test_rejects_unreconciled_profile_totals(self):
        broken = profile_rows()
        for row in broken:
            if row["clock"] == "original_hire" and row["row_type"] == "band" and row["bucket_key"] == "lt_1":
                row["employee_count"] = 41
        with self.assertRaisesRegex(ValueError, "do not reconcile"):
            MODULE.build_evidence_from_rows(audit_rows(), broken)

    def test_rejects_any_visible_band_below_the_privacy_minimum(self):
        original = [29, 35, 30, 35, 30, 30]
        latest = [29, 30, 30, 30, 35, 35]
        with self.assertRaisesRegex(ValueError, "below the minimum cohort"):
            self.build(original_counts=original, latest_counts=latest)

    def test_rejects_sensitive_persisted_keys(self):
        with self.assertRaisesRegex(ValueError, "prohibited key"):
            MODULE.ensure_no_sensitive_keys({"employee_id": 99})
        with self.assertRaisesRegex(ValueError, "prohibited key"):
            MODULE.ensure_no_sensitive_keys({"raw_rows": []})


if __name__ == "__main__":
    unittest.main()
