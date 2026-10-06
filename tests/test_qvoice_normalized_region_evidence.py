"""Offline publication-gate tests for normalized QVoice regional evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_qvoice_normalized_region_evidence.py"
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location("qvoice_normalized_region_builder_test", BUILDER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_bands(total: int) -> list[dict[str, object]]:
    base = total // len(MODULE.Z_BANDS)
    counts = [base] * (len(MODULE.Z_BANDS) - 1)
    counts.append(total - sum(counts))
    percentages = [round(100 * count / total, 6) for count in counts[:-1]]
    percentages.append(round(100 - sum(percentages), 6))
    return [
        {
            "band": label,
            "participant_count": count,
            "percent_of_normalized": percent,
        }
        for (label, _, _), count, percent in zip(MODULE.Z_BANDS, counts, percentages)
    ]


def valid_evidence() -> dict[str, object]:
    waves = []
    for year, expected in MODULE.EXPECTED_WAVES.items():
        total = int(expected["complete"])
        bands = valid_bands(total)
        waves.append(
            {
                "year": year,
                "source_file": f"QVoice-{year}.xlsx",
                "sheet": "Raw data",
                "participant_rows": int(expected["participants"]),
                "source_rows_scanned": int(expected["participants"]),
                "rows_without_participant_key": 0,
                "duplicate_participant_rows": 0,
                "duplicate_conflicting_rows": 0,
                "complete_comparable_participants": total,
                "incomplete_comparable_participants": int(expected["participants"]) - total,
                "complete_comparable_participants_without_region": 0,
                "out_of_domain_non_sentinel_cells": 0,
                "region_wave_cohort_count": MODULE.EXPECTED_REGION_WAVE_COHORTS,
                "minimum_region_wave_cohort_count": 2_305,
                "maximum_region_wave_cohort_count": 9_999,
                "zero_population_standard_deviation_cohort_count": 0,
                "normalized_participants": total,
                "weighted_z_score_mean": 0.0,
                "weighted_population_z_score_standard_deviation": 1.0,
                "z_score_bands": bands,
                "z_score_band_count_total": total,
                "minimum_z_score_band_count": min(
                    int(row["participant_count"]) for row in bands
                ),
            }
        )
    return {
        "artifact": "internal_analysis",
        "evidence_type": "aggregate-only QVoice within-region standardized-score distribution",
        "generated_on": "2026-09-10",
        "outcome": "pass",
        "minimum_shared_cohort": MODULE.MINIMUM_COHORT,
        "source_rule": "QVoice raw Excel workbooks only.",
        "scope": "Respondent-only distribution; no workforce denominator or attrition join.",
        "grain": "participant-wave derived aggregate",
        "formula": {
            "raw_score": "100 x favorable_items / 33",
            "reference_cohort": "stored Region x survey wave, each n >= 30",
            "standardization": "z = (raw_score - mean) / population standard deviation",
            "inclusion_rule": "Exactly 33 valid 0/1 responses.",
        },
        "strict_item_contract": {
            "binary_items_by_wave": {
                str(year): count
                for year, count in MODULE.EXPECTED_BINARY_ITEM_COUNTS.items()
            },
            "strict_common_item_count": MODULE.ITEM_COUNT,
            "header_matching_rule": "strict deterministic match",
            "common_header_bases_sha256": "a" * 64,
        },
        "waves": waves,
        "privacy_checks": {
            "identifiers_persisted": False,
            "employee_rows_persisted": False,
            "response_values_persisted": False,
            "region_labels_persisted": False,
            "all_reference_and_display_cohorts_meet_minimum": True,
        },
        "acceptance_rule": {
            "expected_years": [2024, 2025, 2026],
            "strict_common_item_count": MODULE.ITEM_COUNT,
            "region_wave_cohorts_per_wave": MODULE.EXPECTED_REGION_WAVE_COHORTS,
            "minimum_reference_and_display_cohort": MODULE.MINIMUM_COHORT,
            "zero_duplicate_participant_rows": True,
            "zero_duplicate_conflicting_rows": True,
            "zero_complete_participants_without_region": True,
            "zero_out_of_domain_non_sentinel_cells": True,
            "zero_zero_standard_deviation_cohorts": True,
            "normalized_population_reconciles_to_33_of_33_population": True,
            "weighted_z_mean_zero_and_population_standard_deviation_one": True,
            "no_identifier_response_or_region_label_persistence": True,
        },
    }


class QVoiceNormalizedRegionEvidenceGateTests(unittest.TestCase):
    def test_valid_synthetic_distribution_reconciles_in_ascending_bands(self):
        # Five identical reference cohorts: the five values normalize into one
        # privacy-safe display band each, with n=30 per pooled band.
        scores = [0] * 6 + [1] * 6 + [2] * 6 + [3] * 6 + [4] * 6
        distribution = MODULE.normalized_distribution(
            {f"region-{index}": scores for index in range(5)}
        )
        bands = distribution["z_score_bands"]
        self.assertEqual([row["band"] for row in bands], [item[0] for item in MODULE.Z_BANDS])
        self.assertEqual([row["participant_count"] for row in bands], [30] * 5)
        self.assertEqual(sum(row["participant_count"] for row in bands), 150)
        self.assertAlmostEqual(sum(row["percent_of_normalized"] for row in bands), 100.0)
        self.assertEqual(distribution["minimum_z_score_band_count"], 30)

    def test_rejects_subthreshold_reference_cohort(self):
        scores = [0] * 6 + [1] * 6 + [2] * 6 + [3] * 6 + [4] * 6
        regions = {f"region-{index}": scores for index in range(5)}
        regions["region-0"] = scores[:-1]
        with self.assertRaisesRegex(ValueError, "reference cohort"):
            MODULE.normalized_distribution(regions)

    def test_rejects_zero_standard_deviation_cohort(self):
        regions = {f"region-{index}": [1] * 30 for index in range(5)}
        with self.assertRaisesRegex(ValueError, "zero population standard deviation"):
            MODULE.normalized_distribution(regions)

    def test_rejects_subthreshold_display_band(self):
        # One low score in each cohort creates a published tail with n=5.
        regions = {f"region-{index}": [0] + [1] * 29 for index in range(5)}
        with self.assertRaisesRegex(ValueError, "displayed z-score band"):
            MODULE.normalized_distribution(regions)

    def test_validates_aggregate_only_evidence_and_rejects_private_payload(self):
        evidence = valid_evidence()
        self.assertIs(MODULE.validate_evidence(evidence), evidence)
        serialized = json.dumps(evidence)
        self.assertNotIn("employee_id", serialized)
        self.assertNotIn('"region_labels":', serialized)

        private_payload = copy.deepcopy(evidence)
        private_payload["waves"][0]["employee_id"] = "not allowed"
        with self.assertRaises(ValueError):
            MODULE.validate_evidence(private_payload)

        region_payload = copy.deepcopy(evidence)
        region_payload["waves"][0]["region_labels"] = ["not allowed"]
        with self.assertRaises(ValueError):
            MODULE.validate_evidence(region_payload)

    def test_rejects_duplicates_missing_region_and_nonreconciling_totals(self):
        duplicate = copy.deepcopy(valid_evidence())
        duplicate["waves"][0]["duplicate_participant_rows"] = 1
        with self.assertRaisesRegex(ValueError, "duplicate_participant_rows"):
            MODULE.validate_evidence(duplicate)

        missing_region = copy.deepcopy(valid_evidence())
        missing_region["waves"][0]["complete_comparable_participants_without_region"] = 1
        with self.assertRaisesRegex(ValueError, "complete_comparable_participants_without_region"):
            MODULE.validate_evidence(missing_region)

        totals = copy.deepcopy(valid_evidence())
        totals["waves"][0]["z_score_bands"][-1]["participant_count"] += 1
        with self.assertRaisesRegex(ValueError, "do not reconcile"):
            MODULE.validate_evidence(totals)


if __name__ == "__main__":
    unittest.main()
