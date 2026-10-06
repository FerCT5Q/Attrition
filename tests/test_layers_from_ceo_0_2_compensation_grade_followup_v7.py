"""Publication and deck checks for the 0–2 manager-layer grade follow-up."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
BUILDER = TOOLS / "build_distribution_html_v7.py"
SPEC = importlib.util.spec_from_file_location("distribution_builder_v7_layers_grade_test", BUILDER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LayersFromCeoGradeFollowupV7Tests(unittest.TestCase):
    def test_authorized_internal_exact_grade_evidence_reconciles_to_the_0_2_layer_cohort(self):
        evidence = MODULE.load_layers_from_ceo_0_2_compensation_grade_evidence()
        expected_grades = {
            "M30", "M40", "M50", "M60", "R80", "S50", "S60", "S80", "T80",
            "V10", "V30", "V40", "V70", "V80", "X30", "X40", "X45", "X85",
        }
        self.assertEqual(evidence["deliverable_mode"], "internal_analysis")
        self.assertTrue(evidence["authorization"]["small_cell_exception_applied"])
        self.assertEqual(evidence["cohort"]["employee_count"], 185)
        self.assertEqual(evidence["cohort"]["voluntary_exits"], 19)
        self.assertEqual({row["label"] for row in evidence["rows"]}, expected_grades)
        self.assertEqual(sum(row["employee_count"] for row in evidence["rows"]), 185)
        self.assertEqual(sum(row["voluntary_exits"] for row in evidence["rows"]), 19)
        self.assertTrue(all(row["publication_status"] == "internal_analysis_authorized" for row in evidence["rows"]))
        self.assertEqual(sum(row["employee_count"] < 30 for row in evidence["rows"]), 16)

    def test_generated_deck_has_one_exact_grade_followup_and_contiguous_navigation(self):
        deck = MODULE.OUTPUT_DECK.read_text(encoding="utf-8")
        manifest = json.loads(MODULE.MANIFEST_FILE.read_text(encoding="utf-8"))
        evidence = MODULE.load_layers_from_ceo_0_2_compensation_grade_evidence()
        stages = re.findall(r'<div class="slide-stage" id="([^"]+)"', deck)
        nav = re.findall(r'<button class="nav-pill[^>]* data-slide="(\d+)">(\d+)\. ([^<]+)</button>', deck)
        followup = re.search(
            r'<div class="slide-stage" id="slide-37-followup".*?(?=\n\s*<div class="slide-stage" id="slide-37-span-followup")',
            deck,
            flags=re.S,
        )
        self.assertEqual(len(stages), 44)
        self.assertEqual(len(stages), len(set(stages)))
        self.assertEqual([int(item[0]) for item in nav], list(range(44)))
        self.assertEqual(
            re.findall(r'<span class="nav-section-range">([^<]+)</span>', deck),
            ["1&ndash;2", "3&ndash;4", "5&ndash;16", "17&ndash;23", "24&ndash;35", "36&ndash;44"],
        )
        self.assertEqual(nav[29:33], [
            ("29", "30", "Manager layers to the CEO"),
            ("30", "31", "0&ndash;2 layers: exact compensation grades"),
            ("31", "32", "Direct team size (span)"),
            ("32", "33", "Compensation grade"),
        ])
        self.assertNotIn('id="slide-8"', deck)
        self.assertNotIn('>Team attrition</h2>', deck)
        self.assertNotIn('7. Team attrition</button>', deck)
        self.assertIsNotNone(followup)
        assert followup is not None
        slide = followup.group(0)
        self.assertEqual(slide.count('class="layers-grade-followup-cell '), 18)
        self.assertIn('class="layers-grade-followup-chart"', slide)
        self.assertIn('class="layers-grade-followup-keyline"', slide)
        self.assertNotIn("layers-grade-followup-grid", slide)
        self.assertEqual(slide.count("layers-grade-followup-track"), 18)
        self.assertEqual(slide.count("layers-grade-followup-attrition v6-rate-pill"), 18)
        self.assertEqual(len(re.findall(r'layers-grade-followup-track" aria-hidden="true"><span style="width:[\d.]+%"', slide)), 18)
        self.assertIn('style="width:100.0%"', slide)
        self.assertIn("V10", slide)
        self.assertIn("V30", slide)
        self.assertNotIn("V grade family", slide)
        self.assertNotIn("All other grade families", slide)
        self.assertEqual(slide.count('class="layers-grade-followup-exploratory"'), 16)
        self.assertEqual(slide.count('class="layers-grade-followup-comparable"'), 2)
        for row in evidence["rows"]:
            self.assertIn(f'data-grade="{row["label"]}"', slide)
            self.assertIn(f"n={row['employee_count']:,} &middot; {row['cohort_share_percent']:.1f}%", slide)
            self.assertIn(f"{row['voluntary_exits']:,} exits", slide)
            self.assertIn(f">{row['annual_attrition_rate_percent']:.1f}%</span>", slide)
        self.assertIn("Internal exploratory analysis", slide)
        self.assertIn("grade causes attrition", slide)
        self.assertNotIn("annual_base_pay", slide)
        self.assertNotIn("employee_id", slide)
        self.assertNotIn("manager_employee_id", slide)
        self.assertEqual(manifest["validation"]["slides"], 44)
        self.assertEqual(manifest["validation"]["navigation_items"], 44)
        self.assertTrue(manifest["validation"]["team_attrition_slide_removed"])
        self.assertEqual(manifest["removed_slide_7"]["former_stage_id"], "slide-8")
        self.assertEqual(manifest["inserted_slide_32"]["evidence"]["deliverable_mode"], "internal_analysis")
        self.assertEqual(len(manifest["inserted_slide_32"]["evidence"]["rows"]), 18)
        deck_hash = hashlib.sha256(MODULE.OUTPUT_DECK.read_bytes()).hexdigest()
        self.assertEqual(manifest["output_deck"]["sha256"], deck_hash)


if __name__ == "__main__":
    unittest.main()
