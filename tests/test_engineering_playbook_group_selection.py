import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import engineering_playbook_group_selection as gs  # noqa: E402


def candidate(name, kind, variables, efficiency, groups=10.0, correlation=0.9):
    return {
        "name": name,
        "kind": kind,
        "variables": variables,
        "mean_efficiency": efficiency,
        "mean_groups": groups,
        "stability": {"rank_correlation": correlation, "top_overlap_with_last_fold": 1.0},
    }


class ConcentrationTests(unittest.TestCase):
    def test_perfect_ranking_approaches_one(self):
        exposure = np.ones(1000)
        events = np.zeros(1000)
        events[:10] = 1
        score = -np.arange(1000, dtype=float)
        x, y = gs.concentration_curve(exposure, events, score)
        self.assertGreater(gs.gini(x, y), 0.98)

    def test_constant_score_is_zero(self):
        x, y = gs.concentration_curve(np.ones(100), np.r_[np.ones(10), np.zeros(90)], np.zeros(100))
        self.assertAlmostEqual(gs.gini(x, y), 0.0, places=9)
        self.assertAlmostEqual(gs.share_at(x, y, 0.25), 0.25, places=9)

    def test_random_score_is_near_zero(self):
        rng = np.random.default_rng(0)
        events = rng.binomial(1, 0.05, 20000).astype(float)
        x, y = gs.concentration_curve(np.ones(20000), events, rng.random(20000))
        self.assertLess(abs(gs.gini(x, y)), 0.05)

    def test_one_group_per_cell_has_efficiency_one(self):
        rng = np.random.default_rng(1)
        n = 200
        exposure = rng.integers(400, 900, n).astype(float)
        predictions = rng.uniform(0.01, 0.08, n)
        events = rng.binomial(exposure.astype(int), predictions).astype(float)
        labels = pd.Series([f"g{i}" for i in range(n)])
        result = gs.evaluate_fold(labels, exposure, events, predictions, snapshots=1)
        self.assertAlmostEqual(result["efficiency"], 1.0, places=6)
        self.assertEqual(result["groups"], n)


class GroupingTests(unittest.TestCase):
    def test_small_groups_go_to_rest(self):
        labels = pd.Series(["a", "a", "b", "c"])
        exposure = np.array([200.0, 200.0, 100.0, 500.0])
        out = gs.grouped(labels, exposure, np.zeros(4), exposure * 0.03, snapshots=1, min_people=300)
        self.assertEqual(set(out.index), {"a", "c", gs.REST})
        self.assertEqual(out.loc[gs.REST, "exposure"], 100.0)

    def test_rest_never_in_ranking(self):
        labels = pd.Series(["a", "b"])
        result = gs.evaluate_fold(labels, np.array([1000.0, 10.0]), np.array([10.0, 5.0]), np.array([0.01, 0.5]), snapshots=1)
        self.assertNotIn(gs.REST, result["_risk"].index)
        self.assertEqual(result["groups"], 1)

    def test_coarse_keys(self):
        frame = pd.DataFrame(
            {
                "tenure_playbook_band": ["3-5 years", "10+ years"],
                "team_exits_12m": ["2+", "0"],
                "direct_reports_band": ["0", "6+"],
                "manager_changes_12m": ["1", "0"],
                "time_since_promotion_band": ["promo 1-2 years", "sin promo en historial"],
                "rehire": ["yes", "no"],
                "level_grouped": ["8 - Assoc & Int/Eng", "Misc"],
            }
        )
        keys = gs.coarse_keys(frame)
        self.assertEqual(list(keys.iloc[0]), ["3-5 años", "con salidas", "sin reportes", "entrada", "con cambios de manager", "promoción reciente", "recontratado"])
        self.assertEqual(list(keys.iloc[1]), ["10+ años", "sin salidas", "con reportes", "otro", "sin cambios de manager", "sin promoción registrada", "no recontratado"])
        self.assertEqual(gs.combination_labels(keys, ("antiguedad", "reportes")).iloc[0], "3-5 años · sin reportes")


class SelectionTests(unittest.TestCase):
    def test_parsimony_prefers_fewer_variables(self):
        candidates = [
            candidate("tres", "fixed", ["a", "b", "c"], 0.80),
            candidate("dos", "fixed", ["a", "b"], 0.79),
            candidate("otra", "fixed", ["c", "d"], 0.70),
        ]
        self.assertEqual(gs.select(candidates, 0.02)["winner"], "dos")

    def test_ties_break_on_groups_then_stability(self):
        candidates = [
            candidate("muchos", "fixed", ["a", "b"], 0.80, groups=20),
            candidate("pocos", "fixed", ["c", "d"], 0.80, groups=8, correlation=0.5),
            candidate("pocos estable", "fixed", ["e", "f"], 0.80, groups=8, correlation=0.9),
        ]
        self.assertEqual(gs.select(candidates, 0.02)["winner"], "pocos estable")

    def test_tree_needs_margin(self):
        fixed = candidate("fija", "fixed", ["a", "b"], 0.80)
        close = candidate("árbol", "tree", ["profundidad 3"], 0.81)
        far = candidate("árbol", "tree", ["profundidad 3"], 0.83)
        self.assertEqual(gs.select([fixed, close], 0.02)["winner"], "fija")
        self.assertEqual(gs.select([fixed, far], 0.02)["winner"], "árbol")


if __name__ == "__main__":
    unittest.main()
