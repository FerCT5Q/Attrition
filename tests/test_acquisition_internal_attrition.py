"""Verifica la corrección de tasas, su autorización y la integridad del deck."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_acquisition_entry_evidence as acquisition
import build_distribution_html_v9 as deck_builder


class AcquisitionInternalAttritionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(deck_builder.EVIDENCE.read_text(encoding="utf-8"))
        cls.deck = deck_builder.OUTPUT.read_text(encoding="utf-8")
        cls.source_rows = acquisition.source_query_rows(acquisition.load_json(acquisition.QUERY_RESULTS), acquisition.DISTRIBUTION_QUERY)

    def test_every_rate_uses_the_original_baseline_and_unique_exit_counts(self):
        raw = {r["segment_label"]: r for r in self.source_rows if r["row_type"] == "top_acquisition"}
        for row in self.evidence["top_acquisitions"]:
            annual = row["annual_attrition"]
            source = raw[row["label"]]
            n, e = int(source["baseline_employee_count"]), int(source["voluntary_exit_count"])
            self.assertEqual(annual["baseline_employee_count"], n)
            self.assertEqual(annual["voluntary_exit_count"], e)
            if n:
                expected = Fraction(100 * e, n)
                self.assertLess(abs(Decimal(annual["annual_attrition_rate_percent"]) - Decimal(expected.numerator) / Decimal(expected.denominator)), Decimal("1e-12"))
            else:
                self.assertIsNone(annual["annual_attrition_rate_percent"])
                self.assertEqual(annual["publication_status"], "no_annual_comparable_cohort")

    def test_new_values_and_partition_close(self):
        restored = self.evidence["recalculation"]["restored_categories"]
        self.assertEqual({r["label"]: (r["voluntary_exit_count"], r["baseline_employee_count"], deck_builder.rate_text(r["annual_attrition_rate_percent"])) for r in restored}, {
            "CSR": (21, 658, "3.2%"), "Hercules": (28, 618, "4.5%"),
            "Atheros": (10, 530, "1.9%"), "TDK (SAW/BAW filter and module business)": (1, 307, "0.3%"),
        })
        top = self.evidence["top_acquisitions"]
        self.assertEqual(sum(r["current_employee_count"] for r in top), 7711)
        self.assertEqual(sum(r["annual_attrition"]["baseline_employee_count"] for r in top), 6148)
        self.assertEqual(sum(r["annual_attrition"]["voluntary_exit_count"] for r in top), 193)

    def test_default_presentation_contract_keeps_small_events_suppressed(self):
        row = next(r for r in self.source_rows if r["segment_label"] == "CSR")
        annual = acquisition.as_top_acquisition(row)["annual_attrition"]
        self.assertIsNone(annual["annual_attrition_rate_percent"])
        self.assertNotIn("voluntary_exit_count", annual)
        with self.assertRaisesRegex(ValueError, "salida nueva"):
            acquisition.build(acquisition.OUTPUT, authorization=deck_builder.AUTHORIZATION)

    def test_internal_exception_must_be_explicit_and_match_the_window(self):
        auth = acquisition.load_json(deck_builder.AUTHORIZATION)
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as directory:
            path = Path(directory) / "authorization.json"
            for key, value in (("status", "pending"), ("reporting_mode", "presentation")):
                altered = copy.deepcopy(auth)
                altered[key] = value
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(ValueError):
                    acquisition.authorize_internal_rates(copy.deepcopy(self.evidence), self.source_rows, path)
            altered = copy.deepcopy(auth)
            altered["scope"]["baseline_snapshot"] = "2024-08-25"
            path.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaises(ValueError):
                acquisition.authorize_internal_rates(copy.deepcopy(self.evidence), self.source_rows, path)

    def test_no_cohort_cannot_be_zero_filled(self):
        rows = copy.deepcopy(self.source_rows)
        next(r for r in rows if r["segment_label"] == "Aqua")["voluntary_exit_count"] = 1
        with self.assertRaises(ValueError):
            acquisition.authorize_internal_rates(copy.deepcopy(self.evidence), rows, deck_builder.AUTHORIZATION)
        stage = deck_builder.v8.stage_map(self.deck)[0]["slide-acquisition"]
        self.assertEqual(stage.count(">Sin cohorte</span>"), 5)
        self.assertNotIn("Suppressed", stage)
        self.assertEqual(stage.count('class="v9-rate-counts"'), 6)
        self.assertEqual(len(deck_builder.v8.source_rate_pills(stage)), 8)

    def test_only_slide_8_changes_and_the_original_stays_frozen(self):
        source = deck_builder.SOURCE.read_text(encoding="utf-8")
        before = {m.group("id"): deck_builder.content_without_stage_language(m.group("stage")) for m in deck_builder.v8.STAGE_RE.finditer(source)}
        after = {m.group("id"): deck_builder.content_without_stage_language(m.group("stage")) for m in deck_builder.v8.STAGE_RE.finditer(self.deck)}
        self.assertEqual([k for k in before if before[k] != after.get(k)], ["slide-acquisition"])
        self.assertEqual(len(after), 44)
        self.assertEqual(hashlib.sha256(deck_builder.SOURCE.read_bytes()).hexdigest(), "1f03ea1f427a645e5f84a0e7a7bc74888f76b6991c5f8b41c7920782475d48f6")
        manifest = acquisition.load_json(deck_builder.MANIFEST)
        self.assertEqual(manifest["output"]["deck_sha256"], acquisition.sha256_file(deck_builder.OUTPUT))
        self.assertFalse(manifest["score_v4_change"])
        self.assertEqual(manifest["authorization"]["sha256"], acquisition.sha256_file(deck_builder.AUTHORIZATION))

    def test_corrected_slide_passes_the_presentation_skill_validator(self):
        spec = importlib.util.spec_from_file_location("verify_deck", ROOT / ".agents/skills/build-html-presentation/scripts/verify_deck.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        errors, _ = module.check(deck_builder.PREVIEW.read_text(encoding="utf-8"), "internal_analysis")
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
