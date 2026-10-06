"""Contract checks for the V7 direct-team-span follow-up slide."""

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
SPEC = importlib.util.spec_from_file_location("distribution_builder_v7_direct_team_span_test", BUILDER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DirectTeamSpanFollowupV7Tests(unittest.TestCase):
    def test_frozen_aggregate_evidence_reconciles_and_preserves_privacy(self):
        evidence = MODULE.load_direct_team_span_annual_attrition_evidence()
        coverage = evidence["coverage"]
        bands = evidence["bands"]
        exact = evidence["exact_span_comparison"]

        self.assertEqual(evidence["deliverable_mode"], "internal_analysis")
        self.assertEqual([row["label"] for row in bands], ["1–4", "5–9", "10–14", "15–19", "20–29", "30+"])
        self.assertEqual(coverage["baseline_employee_count"], 45_003)
        self.assertEqual(coverage["eligible_employee_count"], 44_737)
        self.assertEqual(coverage["unresolvable_manager_exclusion_count"], 266)
        self.assertEqual(coverage["baseline_employee_count"], coverage["eligible_employee_count"] + coverage["unresolvable_manager_exclusion_count"])
        self.assertAlmostEqual(coverage["eligible_percent"], 100 * 44_737 / 45_003, places=8)
        self.assertEqual(sum(row["employee_count"] for row in bands), 44_737)
        self.assertEqual(sum(row["voluntary_exits"] for row in bands), 2_480)
        self.assertEqual(sum(row["team_count"] for row in bands), 9_665)
        self.assertTrue(all(row["employee_count"] >= 30 for row in bands))
        self.assertTrue(all(abs(row["annual_attrition_rate_percent"] - 100 * row["voluntary_exits"] / row["employee_count"]) < 0.00011 for row in bands))

        self.assertEqual(
            (exact["five_direct_reports"]["direct_report_count"], exact["five_direct_reports"]["employee_count"], exact["five_direct_reports"]["team_count"]),
            (5, 7_160, 1_432),
        )
        self.assertAlmostEqual(exact["five_direct_reports"]["annual_attrition_rate_percent"], 5.446927374301675, places=10)
        self.assertEqual(
            (exact["twenty_direct_reports"]["direct_report_count"], exact["twenty_direct_reports"]["employee_count"], exact["twenty_direct_reports"]["team_count"]),
            (20, 80, 4),
        )
        self.assertAlmostEqual(exact["twenty_direct_reports"]["annual_attrition_rate_percent"], 8.75, places=10)
        self.assertTrue(exact["twenty_direct_reports"]["exploratory"])
        self.assertTrue(evidence["authorization"]["small_cell_exception_applied"])

        encoded = json.dumps(evidence, ensure_ascii=False).lower()
        for prohibited in ('"employee_id"', '"manager_employee_id"', '"employee_name"', '"manager_name"', '"email"'):
            self.assertNotIn(prohibited, encoded)

    def test_generated_deck_has_contiguous_navigation_and_traceable_span_slide(self):
        deck = MODULE.OUTPUT_DECK.read_text(encoding="utf-8")
        manifest = json.loads(MODULE.MANIFEST_FILE.read_text(encoding="utf-8"))
        evidence = MODULE.load_direct_team_span_annual_attrition_evidence()

        stages = re.findall(r'<div class="slide-stage" id="([^"]+)"', deck)
        nav = re.findall(r'<button class="nav-pill[^>]* data-slide="(\d+)">(\d+)\. ([^<]+)</button>', deck)
        span_match = re.search(
            r'<div class="slide-stage" id="slide-37-span-followup".*?(?=\n\s*<div class="slide-stage" id="slide-38")',
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
        self.assertEqual(nav[29:34], [
            ("29", "30", "Manager layers to the CEO"),
            ("30", "31", "0&ndash;2 layers: exact compensation grades"),
            ("31", "32", "Direct team size (span)"),
            ("32", "33", "Compensation grade"),
            ("33", "34", "Comp ratio"),
        ])
        self.assertNotIn('id="slide-8"', deck)
        self.assertNotIn('>Team attrition</h2>', deck)
        self.assertNotIn('7. Team attrition</button>', deck)
        self.assertIsNotNone(span_match)
        assert span_match is not None
        span_html = span_match.group(0)
        self.assertIn("Direct team size (span): distribution and annual attrition", span_html)
        self.assertIn("Internal exploratory analysis", span_html)
        self.assertIn("team size causes attrition", span_html)
        self.assertEqual(len(re.findall(r'<section class="direct-team-span-band(?:\s|\")', span_html)), 6)
        self.assertIn('class="direct-team-span-chart"', span_html)
        self.assertIn('class="direct-team-span-keyline"', span_html)
        self.assertNotIn("direct-team-span-grid", span_html)
        self.assertEqual(span_html.count("direct-team-span-track"), 6)
        self.assertEqual(span_html.count("direct-team-span-attrition v6-rate-pill"), 6)
        self.assertEqual(len(re.findall(r'direct-team-span-track" aria-hidden="true"><span style="width:[\d.]+%"', span_html)), 6)
        self.assertIn('style="width:100.0%"', span_html)
        self.assertIn("44,737 of 45,003", span_html)
        self.assertIn("266 employees have no resolvable active regular manager", span_html)
        for row in evidence["bands"]:
            self.assertIn(f'data-span-band="{row["label"]}"', span_html)
            self.assertIn(f"n={row['employee_count']:,} &middot; {row['employee_share_percent']:.1f}%", span_html)
            self.assertIn(f"{row['team_count']:,} teams &middot; {row['voluntary_exits']:,} exits", span_html)
            self.assertIn(f">{row['annual_attrition_rate_percent']:.1f}%</span>", span_html)
        self.assertIn('data-exact-span="5"', span_html)
        self.assertIn("n=7,160 &middot; 1,432 teams", span_html)
        self.assertIn('data-exact-span="20"', span_html)
        self.assertIn("n=80 &middot; 4 teams", span_html)
        self.assertIn("exploratory (4 teams)", span_html)
        for prohibited in ("employee_id", "manager_employee_id", "employee_name", "manager_name", "email"):
            self.assertNotIn(prohibited, span_html.lower())

        self.assertEqual(manifest["validation"]["slides"], 44)
        self.assertEqual(manifest["validation"]["navigation_items"], 44)
        self.assertTrue(manifest["validation"]["team_attrition_slide_removed"])
        self.assertEqual(manifest["removed_slide_7"]["former_navigation_slide"], 7)
        self.assertEqual(manifest["validation"]["direct_team_span_bands_visible"], 6)
        self.assertEqual(manifest["validation"]["direct_team_span_eligible_employee_count"], 44_737)
        self.assertEqual(manifest["validation"]["direct_team_span_coverage_exclusion_count"], 266)
        self.assertEqual(manifest["validation"]["direct_team_span_baseline_voluntary_exits"], 2_480)
        self.assertEqual(manifest["inserted_slide_33"]["stage_id"], "slide-37-span-followup")
        self.assertEqual(manifest["inserted_slide_33"]["evidence"]["sha256"], hashlib.sha256(MODULE.DIRECT_TEAM_SPAN_ANNUAL_ATTRITION_EVIDENCE_FILE.read_bytes()).hexdigest())
        self.assertEqual(manifest["inserted_slide_33"]["evidence"]["audit_sql_sha256"], evidence["provenance"]["audit_sql_sha256"])
        self.assertEqual(manifest["output_deck"]["sha256"], hashlib.sha256(MODULE.OUTPUT_DECK.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
