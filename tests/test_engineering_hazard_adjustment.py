import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import engineering_hazard_adjustment as adj  # noqa: E402


def toy_frame(months=24):
    rng = np.random.default_rng(0)
    rows = []
    for m in range(months):
        date = pd.Timestamp("2022-01-25") + pd.DateOffset(months=m)
        for tenure in ["7+ years", "1-3 years"]:
            for exits in ["0", "1"]:
                rate = 0.004 * (2.0 if tenure == "1-3 years" else 1.0) * (1.5 if exits == "1" else 1.0)
                n = 1000
                rows.append(
                    {
                        "snapshot_date": date,
                        "company_tenure_band": tenure,
                        "team_exits_12m": exits,
                        "calendar_month": str(date.month),
                        "exposure_count": n,
                        "event_count": int(rng.binomial(n, rate)),
                    }
                )
    return pd.DataFrame(rows)


class HazardAdjustmentTest(unittest.TestCase):
    def test_no_trend_encoder_drops_time_index(self):
        frame = toy_frame()
        encoder = adj.TrendEncoder.build(frame, ["company_tenure_band"], "none")
        self.assertNotIn("time_index", encoder.columns)
        self.assertEqual(encoder.transform(frame).shape[1], len(encoder.columns))

    def test_frozen_trend_does_not_extrapolate(self):
        frame = toy_frame()
        encoder = adj.TrendEncoder.build(frame, ["company_tenure_band"], "frozen")
        future = frame.assign(snapshot_date=frame["snapshot_date"] + pd.DateOffset(months=12))
        self.assertAlmostEqual(encoder.transform(future)[:, 1].max(), encoder.time_cap)

    def test_recalibration_matches_recent_events(self):
        frame = toy_frame()
        model = adj.fit_variant(frame, ["company_tenure_band", "team_exits_12m"], 0.1, "linear", 12)
        cutoff = frame["snapshot_date"].max() - pd.DateOffset(months=12)
        recent = frame[frame["snapshot_date"] > cutoff]
        predicted = float((model.predict(recent) * recent["exposure_count"]).sum())
        self.assertAlmostEqual(predicted, float(recent["event_count"].sum()), places=3)

    def test_interaction_only_outside_references(self):
        frame = toy_frame()
        references = {c: "x" for pair in adj.INTERACTIONS.values() for c in pair}
        references.update({"company_tenure_band": "7+ years", "team_exits_12m": "0"})
        for column in references:
            if column not in frame:
                frame[column] = "x"
        out = adj.add_interactions(frame, references)
        values = set(out["tenure_x_team_exits"])
        self.assertEqual(values, {adj.REFERENCE_NAME, "1-3 years | 1"})

    def test_promotion_requires_three_folds_and_brier(self):
        def spec(pr, lift, brier):
            return {"summary": {"by_fold": {"pr_auc": pr, "lift_at_10_percent": lift}, "brier_score": brier}}

        base = spec([1, 1, 1, 1], [1, 1, 1, 1], 0.03)
        self.assertTrue(adj.promotion(spec([2, 2, 2, 0], [2, 2, 2, 0], 0.03), base)["promoted"])
        self.assertFalse(adj.promotion(spec([2, 2, 0, 0], [2, 2, 2, 2], 0.03), base)["promoted"])
        self.assertFalse(adj.promotion(spec([2, 2, 2, 2], [2, 2, 2, 2], 0.031), base)["promoted"])

    def test_l2_choice_skips_non_converged_fits(self):
        frame = toy_frame()

        class Fake:
            def __init__(self, l2):
                self.l2, self.converged = l2, l2 >= 1.0

        original = adj.hz.brier_score, adj.hz.six_month_predictions
        try:
            adj.hz.six_month_predictions = lambda model, data: model
            adj.hz.brier_score = lambda data, model: model.l2  # el L2 menor tendría mejor Brier
            self.assertEqual(adj.choose_converged_l2(Fake, frame), 1.0)
        finally:
            adj.hz.brier_score, adj.hz.six_month_predictions = original


if __name__ == "__main__":
    unittest.main()
