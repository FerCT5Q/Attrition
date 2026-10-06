"""Deck-side validation for the frozen manager-layer evidence contract."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
DECK_BUILDER = ROOT / "tools" / "build_distribution_html_v2.py"
SPEC = importlib.util.spec_from_file_location("distribution_builder_layers_test", DECK_BUILDER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_evidence() -> dict[str, object]:
    audit_hash = hashlib.sha256(
        (ROOT / "queries" / "audits" / "layers_from_ceo_snapshot_20260823_distribution.sql").read_bytes()
    ).hexdigest()
    metrics = {
        "universe_node_count": 100,
        "manager_conflict_node_count": 0,
        "self_manager_node_count": 0,
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
        "convergence_rate_percent": 100.0,
        "root_reference_pass": 1,
        "display_eligible_count": 100,
        "display_reconstructed_count": 100,
        "display_unresolved_chain_count": 0,
        "display_approved_root_match_count": 100,
        "maximum_chain_links": 25,
        "published_bucket_count": 2,
        "published_employee_count": 100,
        "minimum_published_bucket_count": 40,
        "minimum_cohort": 30,
    }
    return {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "internal_analysis",
        "variable": "Reconstructed manager layers to CEO",
        "semantic_type": "hierarchy",
        "execution_date": "2026-09-10",
        "snapshot_date": "2026-08-23",
        "population": "active regular employees",
        "grain": "distinct employee snapshot",
        "definition": "Manager-link depth to an approved root.",
        "approved_root_check": {
            "identifier_persisted": False,
            "root_count": 1,
            "convergence_rate_percent": 100.0,
            "outcome": "pass",
        },
        "stored_level_reconciliation": {
            "field": "worker_supervisory_organization_level_from_top",
        },
        "distribution": [
            {"label": "0–2 layers", "lower_depth": 0, "upper_depth": 2, "employee_count": 40, "percent_of_active_regular": 40.0},
            {"label": "3+ layers", "lower_depth": 3, "upper_depth": 3, "employee_count": 60, "percent_of_active_regular": 60.0},
        ],
        "metrics": metrics,
        "provenance": {
            "audit_sql": "queries/audits/layers_from_ceo_snapshot_20260823_distribution.sql",
            "audit_sql_sha256": audit_hash,
            "aggregate_result_sha256": "a" * 64,
            "raw_aggregate_rows_persisted": False,
        },
        "privacy_checks": {
            "identifiers_persisted": False,
            "employee_rows_persisted": False,
            "manager_rows_persisted": False,
            "names_persisted": False,
            "root_identifier_persisted": False,
            "all_displayed_buckets_meet_minimum": True,
            "root_singleton_displayed": False,
        },
        "acceptance_rule": "All publication gates pass.",
        "outcome": "pass",
    }


class LayersFromCeoSlideTests(unittest.TestCase):
    def test_deck_accepts_safe_frozen_evidence_and_renders_ascending_bands(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence_path = Path(temporary_directory) / "layers-evidence.json"
            evidence_path.write_text(json.dumps(valid_evidence()), encoding="utf-8")
            original = MODULE.LAYERS_FROM_CEO_EVIDENCE
            MODULE.LAYERS_FROM_CEO_EVIDENCE = evidence_path
            try:
                evidence, bands = MODULE.layers_from_ceo_distribution_evidence()
                slide = MODULE.layers_from_ceo_slide(32, evidence)
            finally:
                MODULE.LAYERS_FROM_CEO_EVIDENCE = original
        self.assertEqual(bands, [("0–2 layers", 40), ("3+ layers", 60)])
        self.assertIn("Reconstructed manager layers to CEO", slide)
        self.assertIn("Approved-root check", slide)
        self.assertNotIn("CEO/root singleton", slide)

    def test_rebuild_reuses_validated_frozen_evidence_without_a_root_reference(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence_path = Path(temporary_directory) / "layers-evidence.json"
            evidence_path.write_text(json.dumps(valid_evidence()), encoding="utf-8")
            original = MODULE.LAYERS_FROM_CEO_EVIDENCE
            MODULE.LAYERS_FROM_CEO_EVIDENCE = evidence_path
            try:
                label, slide = MODULE.layers_from_ceo_slide_or_support(32)
            finally:
                MODULE.LAYERS_FROM_CEO_EVIDENCE = original
        self.assertEqual(label, "Org layers to CEO")
        self.assertIn("Reconstructed manager layers to CEO", slide)

    def test_full_rebuild_reuses_validated_layers_evidence(self):

        def stage(number: int) -> str:
            return f'<div class="slide-stage" id="slide-{number}">test {number}</div>'

        with tempfile.TemporaryDirectory(dir=ROOT / "output") as temporary_directory:
            output_directory = Path(temporary_directory)
            original_paths = (
                MODULE.OUT,
                MODULE.TARGET,
                MODULE.MANIFEST,
                MODULE.LAYERS_FROM_CEO_EVIDENCE,
            )
            MODULE.OUT = output_directory
            MODULE.TARGET = output_directory / "deck.html"
            MODULE.MANIFEST = output_directory / "deck-manifest.json"
            MODULE.LAYERS_FROM_CEO_EVIDENCE = output_directory / "layers-evidence.json"
            MODULE.LAYERS_FROM_CEO_EVIDENCE.write_text(
                json.dumps(valid_evidence()), encoding="utf-8"
            )
            try:
                patchers = [
                    mock.patch.object(MODULE, "cover", return_value=stage(1)),
                    mock.patch.object(MODULE, "agenda", return_value=stage(2)),
                    mock.patch.object(MODULE, "more_than_1_employee_leaves_evidence", return_value={}),
                    mock.patch.object(MODULE, "more_than_1_employee_leaves_annual_evidence", return_value={}),
                    mock.patch.object(MODULE, "qvoice_comment_evidence", return_value={}),
                    mock.patch.object(MODULE, "qvoice_nonrespondent_evidence", return_value={}),
                    mock.patch.object(MODULE, "application_intensity_by_fiscal_year", return_value=[]),
                    mock.patch.object(MODULE, "transfer_within_past_year_distribution", return_value=[]),
                    mock.patch.object(MODULE, "qvoice_comment_chart_enhancement", return_value=""),
                    mock.patch.object(MODULE, "qvoice_nonrespondent_chart_enhancement", return_value=""),
                    mock.patch.object(MODULE, "application_intensity_chart_enhancement", return_value=""),
                    mock.patch.object(MODULE, "transfer_chart_enhancement", return_value=""),
                    mock.patch.object(MODULE, "team_flag_chart_enhancement_monthly", return_value=""),
                    mock.patch.object(MODULE, "localize_visible_content", side_effect=lambda value: value),
                    mock.patch.object(MODULE, "residual_spanish_visible_text", return_value=[]),
                    mock.patch.object(MODULE, "talent_index_latest_recoverable_distribution", return_value={}),
                    mock.patch.object(MODULE, "residential_manager_distance_evidence", return_value=({}, [])),
                    mock.patch.object(MODULE, "talent_index_manifest_entry", return_value={}),
                    mock.patch.object(MODULE, "residential_manager_distance_manifest_entry", return_value={}),
                    mock.patch.object(
                        MODULE,
                        "qvoice_normalized_region_evidence",
                        return_value={"waves": [], "grain": "aggregate", "outcome": "pass"},
                    ),
                ]
                with ExitStack() as stack:
                    for patcher in patchers:
                        stack.enter_context(patcher)
                    variable_slides = stack.enter_context(
                        mock.patch.object(
                            MODULE,
                            "build_variable_slides",
                            return_value=[(f"test {number}", stage(number)) for number in range(3, 47)],
                        )
                    )
                    MODULE.build()
            finally:
                (
                    MODULE.OUT,
                    MODULE.TARGET,
                    MODULE.MANIFEST,
                    MODULE.LAYERS_FROM_CEO_EVIDENCE,
                ) = original_paths

            manifest = json.loads((output_directory / "deck-manifest.json").read_text(encoding="utf-8"))
        variable_slides.assert_called_once_with()
        self.assertIn("layers-from-ceo-snapshot-20260823", manifest["source_runs"])
        self.assertIn(
            "reconstructed_manager_layers_to_ceo", manifest["frozen_evidence"]
        )


if __name__ == "__main__":
    unittest.main()
