"""Contratos de la calibración R6 y optimizaciones, con datos sintéticos."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import qvoice_horizon_calibration as q
import qvoice_calibrated_model as old
from qvoice_model_validation import fit_model


class HorizonCalibrationTests(unittest.TestCase):
    def test_identity_and_rank(self):
        p = np.linspace(.0001, .8, 1000)
        np.testing.assert_allclose(q.transform_risk(p, 0), p, atol=1e-15)
        for a in [-1.5, -.4, .7, 1.5]:
            self.assertTrue(np.all(np.diff(q.transform_risk(p, a)) > 0))

    def test_equivalent_monthly_hazard_accumulation(self):
        rng = np.random.default_rng(3)
        cumulative_hazards = np.exp(rng.normal(-4, .5, (300, 6)))
        p = 1-np.prod(np.exp(-cumulative_hazards), axis=1)
        for a in [-1., 0., .5]:
            independent = 1-np.prod(np.exp(-np.exp(a)*cumulative_hazards), axis=1)
            np.testing.assert_allclose(q.transform_risk(p, a), independent, atol=1e-14)

    def test_scalar_against_independent_score_root(self):
        rng = np.random.default_rng(57)
        p = rng.uniform(.01, .12, 50000)
        y = rng.binomial(1, q.transform_risk(p, .35))
        result = q.fit_scalar(y, p, [-1.5, 1.5])
        def score(a):
            z = -np.exp(a)*np.log1p(-p)
            return ((1-y)*z-y*z/np.expm1(z)).sum()
        independent = brentq(score, -1.5, 1.5)
        self.assertAlmostEqual(result['log_multiplier'], independent, places=6)
        self.assertLess(result['scalar_fit_log_loss'], result['identity_fit_log_loss'])

    def test_category_matrix_matches_missing_and_unknown(self):
        train = pd.DataFrame({'a': ['v0', 'v1', 'missing', 'v0'], 'b': ['x', 'y', 'x', 'x']})
        encoder = old.CategoryEncoder.fit(train, ['a', 'b'])
        test = pd.DataFrame({'a': ['unknown', 'v1', 'missing', 'v0'], 'b': ['x', 'unknown', 'y', 'x']})
        np.testing.assert_array_equal(q.category_matrix(encoder, test).toarray(), encoder.transform(test).toarray())
        beta = np.arange(len(encoder.columns), dtype=float)*.2
        np.testing.assert_allclose(q.categorical_eta(q.asdict(encoder), beta, test), encoder.transform(test)@beta)

    def test_saved_risk_matches_original_full_calendar(self):
        rng = np.random.default_rng(8)
        n = 6000
        frame = pd.DataFrame({'snapshot_date': rng.choice(pd.date_range('2024-01-01', '2025-12-01', freq='MS'), n),
            'level_grouped': rng.choice(['L1', 'L2'], n), 'tenure_playbook_band': rng.choice(['A', 'B'], n),
            'manager_changes_12m': rng.choice(['0', '1'], n), 'qv_Q4': rng.choice(['v0', 'v1', 'missing'], n),
            'exposure_count': 1, 'event_count': rng.binomial(1, .02, n)})
        features = ['level_grouped', 'tenure_playbook_band', 'manager_changes_12m', 'calendar_month', 'level_x_tenure', 'tenure_x_manager_changes']
        base = fit_model(frame, features, 10.)
        encoder = old.CategoryEncoder.fit(frame, ['qv_Q4'])
        artifact = {'base': old.export_base(base), 'correction': {'kind': 'blocks', 'encoder': q.asdict(encoder), 'beta': [.1, -.3, .2]}, 'calibration': {'intercept': -.2, 'slope': .95}}
        before = deepcopy(artifact)
        np.testing.assert_allclose(q.predict_saved(artifact, frame, True), old.predict_artifact(artifact, frame), atol=1e-12)
        np.testing.assert_allclose(q.base_eta_fast(artifact['base'], frame), old.base_eta(base, frame), atol=1e-12)
        self.assertEqual(artifact, before)

    def test_origins_are_mature_and_keep_reserved_months(self):
        dates = pd.date_range('2024-01-01', '2026-08-01', freq='MS')
        frame = pd.DataFrame({'snapshot_date': dates, 'label_end': dates+pd.offsets.MonthBegin(1),
                              'qvoice_wave': np.where(dates.year >= 2025, '2024', 'ninguna'), 'event_count': 50})
        settings = {'reserved_monthly_intervals': 2, 'minimum_qvoice_training_intervals': 1, 'maximum_calibration_origins': 6}
        self.assertEqual(q.eligible_origins(frame, frame, '2025-08-01', settings), [])
        origins = q.eligible_origins(frame, frame, '2026-01-01', settings)
        self.assertEqual(origins, list(pd.date_range('2025-04-01', '2025-07-01', freq='MS')))
        for date in origins:
            train = q.auxiliary_training(frame, date, settings)
            self.assertLessEqual(train.label_end.max(), date-pd.DateOffset(months=2))
            self.assertLessEqual(date+pd.DateOffset(months=6), pd.Timestamp('2026-01-01'))

    def test_binary_losses_against_manual(self):
        loss = q.binary_losses(np.array([0, 1]), np.array([.2, .8]))
        np.testing.assert_allclose(loss['brier_score'], [.04, .04])
        np.testing.assert_allclose(loss['log_loss'], [-np.log(.8), -np.log(.8)])

    def test_rejects_invalid_probabilities(self):
        for p in [np.array([0]), np.array([1]), np.array([np.nan])]:
            with self.assertRaises(ValueError):
                q.transform_risk(p, 0)


if __name__ == '__main__':
    unittest.main()
