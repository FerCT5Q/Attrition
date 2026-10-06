"""Offline publication-gate tests for reconstructed manager-layer evidence."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_layers_from_ceo_distribution_evidence.py"
SPEC = importlib.util.spec_from_file_location("layers_from_ceo_builder_test", BUILDER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


BASE_METRICS = {
    "active_source_row_count": 100,
    "universe_node_count": 100,
    "duplicate_source_node_count": 0,
    "manager_conflict_node_count": 0,
    "self_manager_node_count": 0,
    "stored_level_conflict_node_count": 0,
    "reconstructed_count": 100,
    "unresolved_chain_count": 0,
    "missing_manager_chain_count": 0,
    "self_manager_chain_count": 0,
    "cycle_chain_count": 0,
    "depth_exceeded_chain_count": 0,
    "manager_conflict_chain_count": 0,
    "root_count": 1,
    "approved_root_resolved_count": 100,
    "nonmatching_approved_root_count": 0,
    "maximum_observed_depth": 3,
    "convergence_rate_percent": 100.0,
    "root_reference_pass": 1,
    "display_eligible_count": 100,
    "display_reconstructed_count": 100,
    "display_unresolved_chain_count": 0,
    "display_approved_root_match_count": 100,
    "stored_level_comparable_count": 100,
    "stored_level_depth_plus_one_match_count": 99,
    "stored_level_depth_plus_one_match_rate_percent": 99.0,
    "maximum_chain_links": 25,
}


def rows(metrics: dict[str, float] | None = None, snapshot: str = "2026-08-23", depths: list[tuple[int, int]] | None = None):
    values = {**BASE_METRICS, **(metrics or {})}
    data = [
        {
            "snapshot_date": snapshot,
            "row_type": "metric",
            "metric": key,
            "depth": None,
            "metric_value": value,
        }
        for key, value in values.items()
    ]
    for depth, count in depths or [(0, 1), (1, 9), (2, 30), (3, 60)]:
        data.append(
            {
                "snapshot_date": snapshot,
                "row_type": "depth_distribution",
                "metric": "display_employee_count",
                "depth": depth,
                "metric_value": count,
            }
        )
    return data


class LayersFromCeoEvidenceGateTests(unittest.TestCase):
    def validated_distribution(self, source_rows):
        metrics, distribution = MODULE.parse_aggregate_rows(source_rows)
        return MODULE.validate_metrics(metrics, distribution)

    def test_pools_root_singleton_and_reconciles_denominator(self):
        distribution = self.validated_distribution(rows())
        self.assertEqual(sum(row["employee_count"] for row in distribution), 100)
        self.assertTrue(all(row["employee_count"] >= 30 for row in distribution))
        self.assertNotIn("0 layers", [row["label"] for row in distribution])
        self.assertEqual(distribution[0]["label"], "0–2 layers")

    def test_rejects_snapshot_mismatch(self):
        with self.assertRaisesRegex(ValueError, "Snapshot mismatch"):
            self.validated_distribution(rows(snapshot="2026-08-16"))

    def test_rejects_root_reference_failure(self):
        with self.assertRaisesRegex(ValueError, "approved CEO root"):
            self.validated_distribution(rows({"root_reference_pass": 0, "root_count": 2}))

    def test_rejects_cycle(self):
        with self.assertRaisesRegex(ValueError, "cycle_chain_count"):
            self.validated_distribution(rows({"cycle_chain_count": 1, "unresolved_chain_count": 1, "reconstructed_count": 99}))

    def test_rejects_unresolved_chain(self):
        with self.assertRaisesRegex(ValueError, "unresolved_chain_count"):
            self.validated_distribution(rows({"unresolved_chain_count": 1, "missing_manager_chain_count": 1, "reconstructed_count": 99}))

    def test_rejects_manager_conflict(self):
        with self.assertRaisesRegex(ValueError, "manager_conflict_node_count"):
            self.validated_distribution(rows({"manager_conflict_node_count": 1, "manager_conflict_chain_count": 1, "unresolved_chain_count": 1, "reconstructed_count": 99}))

    def test_rejects_nonreconciling_display_totals(self):
        with self.assertRaisesRegex(ValueError, "Raw depth totals"):
            self.validated_distribution(rows(depths=[(0, 1), (1, 9), (2, 30), (3, 59)]))


if __name__ == "__main__":
    unittest.main()
