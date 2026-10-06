"""Contract checks for the plain-language V7 cover slide."""

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
SPEC = importlib.util.spec_from_file_location("distribution_builder_v7_intro_test", BUILDER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IntroSlideV7Tests(unittest.TestCase):
    def test_cover_explains_the_universe_and_observed_12_month_attrition(self):
        deck = MODULE.OUTPUT_DECK.read_text(encoding="utf-8")
        manifest = json.loads(MODULE.MANIFEST_FILE.read_text(encoding="utf-8"))
        evidence = MODULE.load_layers_from_ceo_annual_attrition_evidence()
        slide_match = re.search(
            r'<div class="slide-stage" id="slide-1".*?(?=\n\s*<div class="slide-stage" id="slide-2")',
            deck,
            flags=re.S,
        )

        self.assertIsNotNone(slide_match)
        assert slide_match is not None
        slide = slide_match.group(0)
        population = evidence["metrics"]["display_eligible_count"]
        exits = evidence["metrics"]["baseline_voluntary_exits"]
        rate = 100 * exits / population

        self.assertIn('data-v7-intro-population-context="true"', slide)
        self.assertIn("Employee characteristics and attrition", slide)
        self.assertIn("How characteristics are distributed and how voluntary attrition differs across them", slide)
        self.assertIn("What may be related", slide)
        self.assertIn("Each slide shows how employees are distributed across categories and, where available, the voluntary attrition rate for each category.", slide)
        self.assertIn("Employees with Regular status who were active at the date used for each slide.", slide)
        self.assertIn("The percentage who chose to leave the company. Other types of departure are not included.", slide)
        self.assertIn(f"{rate:.1f}% &middot; {exits:,} employees chose to leave in the 12 months ending 23 Aug 2026.", slide)
        self.assertIn(f"We start with {population:,} Regular employees active on 24 Aug 2025 and follow them to 23 Aug 2026.", slide)
        self.assertIn("Most distributions show employees active in August 2026.", slide)
        self.assertIn("Each slide states its own time period.", slide)
        for obsolete_or_technical in ("reviewed V5 evidence", "What each variable means", "model-planning discussion", "RF360", "next 12 months"):
            self.assertNotIn(obsolete_or_technical, slide)

        self.assertIn('data-slide="0">1. Employee characteristics and attrition</button>', deck)
        self.assertEqual(manifest["updated_slide_1"]["baseline_employee_count"], population)
        self.assertEqual(manifest["updated_slide_1"]["voluntary_exit_count"], exits)
        self.assertAlmostEqual(manifest["updated_slide_1"]["annual_voluntary_attrition_rate_percent"], rate, places=4)
        self.assertEqual(
            manifest["updated_slide_1"]["evidence"]["sha256"],
            hashlib.sha256(MODULE.LAYERS_FROM_CEO_ANNUAL_ATTRITION_EVIDENCE_FILE.read_bytes()).hexdigest(),
        )
        self.assertEqual(manifest["output_deck"]["sha256"], hashlib.sha256(MODULE.OUTPUT_DECK.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
