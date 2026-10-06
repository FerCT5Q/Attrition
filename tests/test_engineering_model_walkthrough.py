import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import engineering_model_walkthrough as wt  # noqa: E402
import engineering_playbook_group_selection as gs  # noqa: E402


class FormulaTests(unittest.TestCase):
    def test_cumulative_matches_hand_formula(self):
        h = np.array([0.009, 0.010, 0.011, 0.010, 0.009, 0.011])
        expected = 1 - (1 - 0.009) * (1 - 0.010) * (1 - 0.011) * (1 - 0.010) * (1 - 0.009) * (1 - 0.011)
        self.assertAlmostEqual(float(wt.cumulative(h)), expected, places=12)

    def test_cumulative_is_row_wise(self):
        h = np.array([[0.0] * 6, [0.5] * 6])
        np.testing.assert_allclose(wt.cumulative(h), [0.0, 1 - 0.5**6])

    def test_two_averages_differ_little_for_small_hazards(self):
        rng = np.random.default_rng(0)
        hazards = rng.uniform(0.002, 0.012, (500, 6))
        people = rng.integers(30, 200, 500)
        out = wt.group_summary(people, hazards)
        self.assertGreaterEqual(out["r6_formula_percent"], out["r6_mean_of_people_percent"] - 1e-9)
        self.assertLess(out["r6_formula_percent"] - out["r6_mean_of_people_percent"], 0.05)

    def test_observed_only_with_enough_events(self):
        hazards = np.full((2, 6), 0.005)
        few = wt.group_summary(np.array([400, 400]), hazards, np.array([10, 19]))
        self.assertFalse(few["observed_events_published"])
        self.assertNotIn("observed_6m_percent", few)
        many = wt.group_summary(np.array([400, 400]), hazards, np.array([10, 20]))
        self.assertEqual(many["observed_events"], 30)
        self.assertAlmostEqual(many["observed_6m_percent"], 100 * 30 / 800, places=3)


class PrivacyTests(unittest.TestCase):
    def test_example_people_are_fictitious_and_fall_in_their_group(self):
        self.assertEqual(len(wt.EXAMPLE_PEOPLE), 6)
        references = {"level_grouped": "7 - Senior & Lead", "tenure_playbook_band": "5-10 years", "manager_changes_12m": "0"}
        frame = wt.example_frame(wt.EXAMPLE_PEOPLE, pd.Timestamp("2026-01-25"), references)
        self.assertNotIn("employee_id", frame.columns)
        labels = gs.combination_labels(gs.coarse_keys(frame), ("antiguedad", "salidas_equipo", "nivel"))
        self.assertEqual(list(labels), [wt.GROUPS[g] for _, g, _ in wt.EXAMPLE_PEOPLE])
        # Fernando (3-5 años, nivel 8): interacción nivel × antigüedad activa; Leah (5-10 años, nivel 7) es referencia.
        self.assertEqual(frame.loc[0, "level_x_tenure"], "8 - Assoc & Int/Eng | 3-5 years")
        self.assertEqual(frame.loc[2, "level_x_tenure"], "ref")

    def test_small_groups_go_to_rest(self):
        labels = pd.Series(["a", "b", "c"])
        people = np.array([299.0, 300.0, 1000.0])
        out = gs.grouped(labels, people, np.zeros(3), people * 0.03, 1, gs.MIN_GROUP_PEOPLE)
        self.assertIn(gs.REST, out.index)
        self.assertNotIn("a", out.index)

    def test_dots_add_up(self):
        people = [37221 - 1406, 1406]
        self.assertEqual(sum(wt.dot_count(p) for p in people), 372)


class MonthTests(unittest.TestCase):
    def test_january_snapshot_covers_february_to_july(self):
        self.assertEqual(wt.month_labels(pd.Timestamp("2026-01-25")), ["feb", "mar", "abr", "may", "jun", "jul"])


if __name__ == "__main__":
    unittest.main()
