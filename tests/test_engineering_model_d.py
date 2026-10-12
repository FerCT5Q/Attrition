"""Pruebas sintéticas de D; no consultan ni guardan datos de empleados."""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import engineering_model_c as c
import engineering_model_d as d
import qvoice_calibrated_model as qmodel


class ModelDTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT/'config/engineering_model_d_20261010.json').read_text(encoding='utf-8'))
        dates = pd.to_datetime(['2025-01-26','2025-02-23','2025-03-23','2025-04-27','2025-05-25','2025-06-22'])
        n = 120
        rng = np.random.default_rng(20261010)
        self.frame = pd.DataFrame({
            'snapshot_date': np.repeat(dates, n),
            'label_end': np.repeat(dates + pd.DateOffset(months=1), n),
            'person_key': np.tile([f'p{i}' for i in range(n)], len(dates)),
            'calendar_month': np.repeat(dates.month.astype(str), n),
            'level': rng.choice(['entry','senior'], n*len(dates)),
            'hr': rng.choice(['0','1','2+'], n*len(dates)),
            'qv': rng.choice(['v0','v1','missing'], n*len(dates))})
        self.frame['y_next'] = rng.binomial(1, .18, len(self.frame))
        self.frame['r6_end'] = self.frame.snapshot_date + pd.DateOffset(months=6)
        self.frame['y_6m'] = rng.binomial(1, .25, len(self.frame))
        design = c.Design.fit(self.frame, ['level','calendar_month'], {})
        beta, iterations = c.fit_sparse(design.matrix(self.frame), self.frame.y_next, 1)
        self.model = c.Model(design, beta, ['level','calendar_month'], 1, iterations)

    def test_vector_penalty_separates_hr_and_q(self):
        columns = ['intercept','hr=1','hr=2+','qv=v1']
        actual = d.penalty_vector(columns, {'hr'}, .1, 10, 8)
        np.testing.assert_allclose(actual, [0,.8,.8,80])

    def test_offset_fit_with_no_signal_keeps_probabilities_finite(self):
        x = sparse.csr_matrix(np.ones((1000,1)))
        y = np.r_[np.ones(40), np.zeros(960)]
        offset = np.repeat(np.log(-np.log1p(-.04)), len(y))
        beta, _, unique = d.penalized_fit(x, y, offset, [0])
        self.assertEqual(unique, 1)
        p = c.hazard(offset + x@beta)
        self.assertTrue(np.isfinite(p).all())
        self.assertAlmostEqual(float(p.mean()), .04, places=8)

    def test_zero_correction_reproduces_c(self):
        zero = np.zeros(len(self.frame))
        np.testing.assert_allclose(d.cq.risk(self.model, self.frame, zero), self.model.risk(self.frame), atol=1e-12)

    def test_six_month_accumulation_is_probability(self):
        correction = np.linspace(-1, 1, len(self.frame))
        risk = d.cq.risk(self.model, self.frame, correction)
        self.assertTrue(((risk > 0) & (risk < 1)).all())
        self.assertGreater(np.corrcoef(correction, risk)[0,1], .5)

    def test_monthly_fallback_is_explicit(self):
        frame = self.frame.copy()
        frame['y_6m'] = np.nan
        local = deepcopy(self.config)
        local['selection']['monthly_fallback_snapshots'] = 3
        core, valid, mode, dates = d.selection_split(frame, '2025-07-31', local)
        self.assertEqual(mode, 'monthly_fallback')
        self.assertEqual(len(dates), 3)
        self.assertLessEqual(core.label_end.max(), valid.snapshot_date.min())

    def test_r6_split_never_uses_future_outcome(self):
        local = deepcopy(self.config)
        local['selection']['r6_snapshots'] = 3
        core, valid, mode, _ = d.selection_split(self.frame, '2026-01-01', local)
        self.assertEqual(mode, 'r6')
        self.assertTrue((valid.r6_end <= pd.Timestamp('2026-01-01')).all())
        self.assertLessEqual(core.label_end.max(), valid.snapshot_date.min())

    def test_category_roundtrip_contains_parameters_only(self):
        encoder = qmodel.CategoryEncoder.fit(self.frame, ['hr','qv'])
        spec = {'id':'synthetic','features':['hr','qv'],'l2_hr':1.,'l2_q':10.}
        fitted = {'link':'cloglog','encoder':encoder,'beta':np.zeros(len(encoder.columns)),
                  'iterations':1,'unique_design_offset_rows':1,'l2_hr':1.,'l2_q':10.,'features':['hr','qv']}
        artifact = d.artifact_json(self.model.artifact(), fitted, spec, '2025-07-01')
        text = json.dumps(d.groups.native(artifact))
        self.assertNotIn('person_key', text)
        self.assertNotIn('y_next', text)
        self.assertFalse(artifact['employee_level_rows_persisted'])

    def test_history_sql_has_temporal_and_one_to_one_guards(self):
        sql = (ROOT/self.config['history_query']).read_text(encoding='utf-8')
        c.db.validate_readonly(sql)
        self.assertIn('__RUN_SALT__', sql)
        self.assertIn('e.known_date <= p.snapshot_date', sql)
        self.assertIn('x.known_date<=p.snapshot_date', sql.replace(' ',''))
        self.assertIn('GROUPBY1,2', sql.replace(' ',''))
        final = sql[sql.rfind('SELECT p.snapshot_date'):]
        self.assertNotIn(' AS employee_id', final)
        self.assertNotIn('manager_id AS', final)

    def test_audit_queries_define_zero_violation_rules(self):
        names = self.config['audit_queries']
        self.assertEqual(len(names), 4)
        joined = '\n'.join((ROOT/name).read_text(encoding='utf-8') for name in names)
        for token in ['monotonicity_violations','band_consistency_violations',
                      'negative_span_violations','nonpositive_denominator_violations']:
            self.assertIn(token, joined)


if __name__ == '__main__':
    unittest.main()
