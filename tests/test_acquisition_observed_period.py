"""Protege tasas parciales, cohorte fija y ausencia de seguimiento en la lámina 8."""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_distribution_html_v10 as builder


class AcquisitionObservedPeriodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = yaml.safe_load(builder.PLAN.read_text(encoding="utf-8"))
        cls.rows = builder.read_json(builder.RAW)["rows"]
        cls.periods = builder.calculate_periods(cls.rows, cls.plan)
        cls.deck = builder.OUTPUT.read_text(encoding="utf-8")

    def test_observed_rates_count_people_not_repeated_exit_events(self):
        expected = {"Aqua": (1229, 102, "8.3%*"), "NAPS": (4, 0, "0%*"),
                    "Arduino": (163, 2, "1.2%*"), "Augentix Inc.": (130, 12, "9.2%*")}
        for row in self.periods:
            if row["category_label"] not in expected:
                continue
            n, exits, text = expected[row["category_label"]]
            self.assertEqual((row["baseline_employee_count"], row["voluntary_exit_count"], row["display_rate"]), (n, exits, text))
            exact = Fraction(100 * exits, n)
            self.assertLess(abs(Decimal(row["observed_attrition_rate_percent"]) - Decimal(exact.numerator) / Decimal(exact.denominator)), Decimal("1e-12"))
        aqua = next(r for r in self.periods if r["category_label"] == "Aqua")
        self.assertEqual((aqua["raw_voluntary_event_row_count"], aqua["unique_employee_date_event_count"], aqua["voluntary_exit_count"]), (598, 103, 102))

    def test_window_is_displayed_without_annualization(self):
        self.assertEqual({r["category_label"]: (r["followup_days"], r["display_months"]) for r in self.periods},
                         {"Aqua": (238, "7.8"), "NAPS": (210, "6.9"), "Moonshot": (0, "0"),
                          "Arduino": (147, "4.8"), "Augentix Inc.": (147, "4.8")})
        self.assertTrue(all(r["annualized"] is False for r in self.periods))
        altered = copy.deepcopy(self.plan)
        altered["annualization"] = True
        with self.assertRaisesRegex(ValueError, "anualizarse"):
            builder.calculate_periods(self.rows, altered)

    def test_real_zero_differs_from_no_followup(self):
        naps = next(r for r in self.periods if r["category_label"] == "NAPS")
        moonshot = next(r for r in self.periods if r["category_label"] == "Moonshot")
        self.assertEqual(naps["display_rate"], "0%*")
        self.assertEqual(naps["postbaseline_snapshot_count"], 7)
        self.assertEqual(moonshot["display_rate"], "—")
        self.assertIsNone(moonshot["observed_attrition_rate_percent"])
        altered = copy.deepcopy(self.rows)
        next(r for r in altered if r["category_label"] == "Moonshot")["observed_attrition_rate_percent"] = "0"
        with self.assertRaisesRegex(ValueError, "Cero seguimiento"):
            builder.calculate_periods(altered, self.plan)

    def test_later_entrants_do_not_change_the_starting_cohort(self):
        naps = next(r for r in self.periods if r["category_label"] == "NAPS")
        self.assertEqual((naps["baseline_employee_count"], naps["current_employee_count"], naps["current_employees_outside_starting_cohort"]), (4, 178, 174))
        stage = builder.v9.v8.stage_map(self.deck)[0]["slide-acquisition"]
        self.assertIn("cohorte inicial de 4 empleados", stage)
        self.assertIn("0 / 4", stage)

    def test_rejects_unreconciled_events_and_inconsistent_window(self):
        for key, value in (("independent_voluntary_exit_count", 103), ("followup_days", 365), ("contradictory_baseline_employee_count", 1)):
            altered = copy.deepcopy(self.rows)
            altered[0][key] = value
            with self.assertRaises(ValueError):
                builder.calculate_periods(altered, self.plan)

    def test_partial_rates_are_gray_and_original_annual_rates_remain(self):
        stage = builder.v9.v8.stage_map(self.deck)[0]["slide-acquisition"]
        pills = re.findall(r'<span class="(v8-acquisition-rate[^"]*)"[^>]*>([^<]+)</span>', stage)
        self.assertEqual([text for classes, text in pills if "v8-reference-unavailable" not in classes],
                         ["3.1%", "5.9%", "2.2%", "3.2%", "4.5%", "1.9%", "0.3%", "5.4%"])
        partial = [(classes, text) for classes, text in pills if "v10-partial-rate" in classes]
        self.assertEqual([text for _, text in partial], ["8.3%*", "0%*", "1.2%*", "9.2%*"])
        self.assertTrue(all("v8-reference-unavailable" in classes and not re.search(r"attr-(low|mid|high)", classes) for classes, _ in partial))
        self.assertEqual(stage.count('data-window-kind="no_followup"'), 1)

    def test_only_slide_8_changes_and_evidence_is_traceable(self):
        original = builder.SOURCE.read_text(encoding="utf-8")
        before = {m.group("id"): m.group("stage").strip() for m in builder.v9.v8.STAGE_RE.finditer(original)}
        after = {m.group("id"): m.group("stage").strip() for m in builder.v9.v8.STAGE_RE.finditer(self.deck)}
        self.assertEqual([key for key in before if before[key] != after.get(key)], ["slide-acquisition"])
        self.assertEqual(len(after), 44)
        self.assertEqual(builder.digest(builder.SOURCE), "9dff4c0069aa4f8de8f31678e69160b062cbe40ad48c7702328118fded3472be")
        manifest = builder.read_json(builder.MANIFEST)
        self.assertEqual(manifest["output"]["deck_sha256"], builder.digest(builder.OUTPUT))
        self.assertEqual(manifest["observed_period_evidence"]["sha256"], builder.digest(builder.EVIDENCE))
        self.assertFalse(manifest["score_v4_change"])
        helper_spec = importlib.util.spec_from_file_location("readonly", ROOT / ".codex/skills/attrition-redshift-db/scripts/run_readonly_query.py")
        helper = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(helper)
        self.assertTrue(helper.validate_readonly(builder.SQL.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
