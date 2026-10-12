"""Invariantes del experimento B incremental con datos exclusivamente sintéticos."""
import copy
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd
from scipy import sparse
from threadpoolctl import threadpool_limits

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import engineering_b_incremental as inc
import engineering_model_c as base
import b_incremental_qvoice as q
import b_incremental_data as data
import qvoice_calibrated_model as previous_q


def synthetic(periods=36,people=600):
    rng = np.random.default_rng(31415)
    dates = pd.date_range('2023-01-31',periods=periods,freq='ME')
    n = len(dates)*people
    f = pd.DataFrame({'snapshot_date':np.repeat(dates,people),
                      'person_key':np.tile([f'synthetic-{i}' for i in range(people)],len(dates))})
    f['label_end'] = f.snapshot_date+pd.DateOffset(months=1)
    f['r6_end'] = f.snapshot_date+pd.DateOffset(months=6)
    f['calendar_month'] = f.snapshot_date.dt.month.astype(str)
    f['level_grouped'] = rng.choice(['L1','L2'],n)
    f['tenure_playbook_band'] = rng.choice(['1-2 years','5-10 years'],n)
    f['manager_changes_12m'] = rng.choice(['0','1'],n)
    f['team_exits_12m'] = rng.choice(['0','1'],n)
    f['direct_reports_band'] = rng.choice(['0','1-5'],n)
    f['time_since_promotion_band'] = rng.choice(['promo <1 year','promo 3+ years'],n)
    f['rehire'] = rng.choice(['yes','no'],n)
    config = base.read(inc.DEFAULT)
    for feature in inc.hr_candidates(config):
        f[feature] = rng.choice(['low','high'],n)
    probability = np.where(f.region.eq('high'),.1,.045)
    f['y_next'] = rng.binomial(1,probability)
    f['y_6m'] = rng.binomial(1,1-(1-probability)**6)
    for feature in inc.q_candidates(config):
        f[feature] = rng.choice(['v0','v1','no_linked_row'],n,p=[.2,.65,.15])
    f['person_key'] = f.person_key.astype('category')
    return f,config


class IncrementalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame,cls.config = synthetic()
        cls.limits = threadpool_limits(limits=1)

    @classmethod
    def tearDownClass(cls):
        cls.limits.restore_original_limits()

    def test_base_terms_and_interactions_are_mandatory(self):
        features = inc.mandatory_features(['region'],self.config)
        self.assertEqual(features[:10],list(inc.B_TERMS))
        altered = copy.deepcopy(self.config)
        altered['base_features'].remove('tenure_x_manager_changes')
        with self.assertRaises(ValueError):
            inc.mandatory_features(['region'],altered)
        with self.assertRaises(ValueError):
            inc.mandatory_features(['gender'],self.config)

    def test_temporal_r6_split_excludes_unmatured_labels(self):
        core,valid,mode,record = inc.temporal_split(self.frame,'2025-08-01',self.config)
        self.assertEqual(mode,'r6')
        self.assertLessEqual(core.label_end.max(),valid.snapshot_date.min())
        self.assertLessEqual(valid.r6_end.max(),pd.Timestamp('2025-08-01'))
        self.assertEqual(valid.snapshot_date.nunique(),3)

    def test_qvoice_monthly_fallback_is_explicit_and_separated(self):
        core,valid,mode,record = inc.temporal_split(self.frame,'2025-08-01',self.config,qvoice=True)
        self.assertEqual(mode,'monthly_fallback')
        self.assertLessEqual(core.label_end.max(),valid.snapshot_date.min())
        self.assertGreaterEqual(core.snapshot_date.min(),pd.Timestamp('2025-01-01'))
        self.assertLessEqual(valid.label_end.max(),pd.Timestamp('2025-08-01'))

    def test_future_outcomes_do_not_change_the_selection_split(self):
        core,valid,_,_ = inc.temporal_split(self.frame,'2025-08-01',self.config)
        altered = self.frame.copy()
        altered.loc[altered.label_end>pd.Timestamp('2025-08-01'),'y_next'] = 1
        altered.loc[altered.r6_end>pd.Timestamp('2025-08-01'),'y_6m'] = 1
        later_core,later_valid,_,_ = inc.temporal_split(altered,'2025-08-01',self.config)
        np.testing.assert_array_equal(core.y_next,later_core.y_next)
        np.testing.assert_array_equal(valid.y_6m,later_valid.y_6m)

    def test_pool_is_learned_from_training_only_and_does_not_mutate(self):
        train = pd.DataFrame({'person_key':['a','b','c'],'feature':['kept','kept','rare']})
        pool = inc.RarePool.fit(train,['feature'],2)
        future = pd.DataFrame({'feature':['future','kept','rare']})
        mapped = pool.apply(future)
        self.assertEqual(mapped.feature.astype(str).tolist(),['(other)','kept','(other)'])
        self.assertEqual(future.feature.tolist(),['future','kept','rare'])
        self.assertNotIn('future',pool.keep['feature'])

    def test_pairs_and_triples_include_joint_candidates_without_greedy_gate(self):
        candidates = inc.combination_sets(['a','b','c','d','e','f'],3)
        self.assertEqual(len(candidates),35)
        self.assertIn(['a','b'],candidates)
        self.assertIn(['d','e','f'],candidates)

    def test_more_features_cannot_force_adoption(self):
        b = {'id':'B','status':'ok','additions':[],
             'metrics':{'brier_score':.04,'pr_auc':.2,'log_loss':.15}}
        bad = {'id':'B + bad','status':'ok','additions':['bad'],
               'metrics':{'brier_score':.05,'pr_auc':.19,'log_loss':.14}}
        winner = inc.choose([b,bad],b,self.config,'monthly_fallback')
        self.assertIs(winner,b)

    def test_aggregate_capacity_diagnostic_does_not_break_ties_by_outcome(self):
        frame=pd.DataFrame({'snapshot_date':[pd.Timestamp('2024-01-31')]*10+[pd.Timestamp('2024-02-29')]*10,
                            'y_6m':[1,1,1,0,0,0,0,0,0,0]*2})
        self.assertAlmostEqual(inc.aggregate_score_capture(frame,np.full(20,.1),.3),30.)
        changed=frame.copy()
        changed['y_6m']=frame.y_6m.iloc[::-1].to_numpy()
        self.assertAlmostEqual(inc.aggregate_score_capture(changed,np.full(20,.1),.3),30.)

    def test_hr_export_retains_base_and_reproduces_risk(self):
        fitted = inc.fit_hr(self.frame,'2024-01-01',['region'],1.,self.config)
        valid = self.frame.loc[self.frame.snapshot_date>=pd.Timestamp('2024-01-01')].iloc[:500]
        restored = inc.HRModel.restore(fitted.artifact())
        self.assertTrue(set(inc.B_TERMS)<=set(restored.model.features))
        np.testing.assert_allclose(restored.risk(valid),fitted.risk(valid),atol=1e-12)
        self.assertNotIn('person_key',str(fitted.artifact()))

    def test_zero_correction_is_exactly_the_base_six_month_formula(self):
        fitted = inc.fit_hr(self.frame,'2024-01-01',[],1.,self.config)
        valid = self.frame.iloc[-600:]
        np.testing.assert_allclose(inc.risk_with_correction(fitted,valid,np.zeros(len(valid))),fitted.risk(valid),atol=1e-12)

    def test_hr_combination_roundtrip_when_selection_order_differs_from_catalog(self):
        train = base.train_before(self.frame,'2024-01-01')
        valid = self.frame.iloc[-600:]
        context = inc.HRContext(train,valid,self.config,'2024-01-01')
        additions = ['job_family_detail','region','prior_experience_band']
        fitted,p,_ = context.fit(additions,1.)
        restored = inc.HRModel.restore(fitted.artifact())
        np.testing.assert_allclose(restored.risk(valid),p,atol=1e-12,rtol=0)
        direct = inc.fit_hr(self.frame,'2024-01-01',additions,1.,self.config)
        np.testing.assert_allclose(restored.risk(valid),direct.risk(valid),atol=1e-10,rtol=0)

    def test_playbook_block_is_fitted_and_exported_with_all_base_terms(self):
        config = copy.deepcopy(self.config)
        config['extra_hr_queries'] = [{'name':'synthetic-playbook','features':['new_playbook_feature']}]
        frame = self.frame.copy()
        frame['new_playbook_feature'] = np.where(np.arange(len(frame))%3==0,'first','second')
        train = base.train_before(frame,'2024-01-01')
        valid = frame.iloc[-600:]
        context = inc.HRContext(train,valid,config,'2024-01-01')
        fitted,p,_ = context.fit(['new_playbook_feature','region'],1.)
        artifact = fitted.artifact()
        self.assertTrue(set(inc.B_TERMS)<=set(artifact['model']['features']))
        self.assertIn('new_playbook_feature',artifact['model']['features'])
        np.testing.assert_allclose(inc.HRModel.restore(artifact).risk(valid),p,atol=1e-12,rtol=0)

    def test_playbook_join_rejects_missing_or_duplicated_person_snapshots(self):
        base_frame = pd.DataFrame({'snapshot_date':[pd.Timestamp('2025-01-31')]*2,'person_key':['synthetic-a','synthetic-b']})
        missing = base_frame.iloc[:1].assign(new_feature='value')
        with self.assertRaises(RuntimeError):
            data.join_frame(base_frame,missing,'synthetic')
        duplicate = pd.concat([base_frame,base_frame.iloc[:1]],ignore_index=True).assign(new_feature='value')
        with self.assertRaises(pd.errors.MergeError):
            data.join_frame(base_frame,duplicate,'synthetic')

    def test_qvoice_combination_roundtrip_when_selection_order_differs_from_catalog(self):
        train = base.train_before(self.frame,'2024-01-01')
        valid = self.frame.iloc[-600:]
        hr = inc.fit_hr(self.frame,'2024-01-01',[],1.,self.config)
        context = q.Context(train,valid,hr,self.config,mode='monthly_fallback')
        additions = ['qv_M16','qv_M02','qv_mean33']
        fitted,p,_ = context.fit(additions,1.)
        artifact = q.artifact(hr,fitted,{'additions':additions,'kind':'q'},'2024-01-01')
        expected_offset = np.log(-np.log1p(-p))-hr.eta(valid)
        expected_r6 = inc.risk_with_correction(hr,valid,expected_offset)
        np.testing.assert_allclose(q.predict_saved(artifact,valid),expected_r6,atol=1e-12,rtol=0)

    def test_compressed_offset_agrees_with_independent_uncompressed_solver(self):
        rng = np.random.default_rng(9)
        x = sparse.csr_matrix(np.column_stack([np.ones(1800),rng.binomial(1,.4,1800),rng.binomial(1,.2,1800)]))
        offset = rng.choice([-3.5,-3.,-2.7],1800)
        y = rng.binomial(1,base.hazard(offset+np.asarray(x@np.array([.2,.4,-.3])).ravel()))
        compressed,_,_ = inc.weighted_offset_fit(x,y,offset,1.,8.)
        independent,converged,_ = previous_q.fit_offset(x,y,offset,8.)
        self.assertTrue(converged)
        np.testing.assert_allclose(compressed,independent,atol=1e-7)

    def test_qvoice_export_roundtrip_and_availability_have_no_content(self):
        train = base.train_before(self.frame,'2024-01-01')
        valid = self.frame.iloc[-600:]
        hr = inc.fit_hr(self.frame,'2024-01-01',[],1.,self.config)
        context = q.Context(train,valid,hr,self.config,mode='monthly_fallback')
        fitted,p,_ = context.fit(['qv_M16'],1.)
        artifact = q.artifact(hr,fitted,{'additions':['qv_M16'],'kind':'q'},'2024-01-01')
        p6 = inc.risk_with_correction(hr,valid,fitted.offset(valid))
        np.testing.assert_allclose(q.predict_saved(artifact,valid),p6,atol=1e-12)
        transformed = q.prepared(pd.DataFrame({'qv_M16':['v0','v1','no_linked_row']}),['qv_M16'])
        self.assertEqual(transformed.availability_qv_M16.tolist(),['available','available','no_linked_row'])

    def test_regional_reference_does_not_use_other_snapshots(self):
        f = self.frame.iloc[:1200].copy()
        for i in range(1,34):
            f[f'qv_M{i:02d}'] = np.where(np.arange(len(f))%(i+2)==0,'v0','v1')
        f['qv_mean33'] = '80–89'
        f['region'] = 'one-region'
        altered = f.copy()
        for i in range(1,34):
            altered.loc[altered.snapshot_date>altered.snapshot_date.min(),f'qv_M{i:02d}'] = 'v0'
        data.regional_qvoice(f,self.config)
        data.regional_qvoice(altered,self.config)
        first = f.snapshot_date==f.snapshot_date.min()
        np.testing.assert_array_equal(f.loc[first,'qv_region_relative'],altered.loc[first,'qv_region_relative'])

    def test_sql_is_read_only_and_output_contains_no_raw_pay_or_id(self):
        for key in ['base_query','history_query','pending_query']:
            sql = (base.ROOT/self.config[key]).read_text(encoding='utf-8')
            base.db.validate_readonly(sql)
            self.assertIn('__RUN_SALT__',sql)
        sql = (base.ROOT/self.config['pending_query']).read_text(encoding='utf-8').split('-- MODEL_OUTPUT')[1]
        self.assertNotIn(' AS employee_id',sql)
        self.assertNotIn('fte_annual_base_pay',sql)
        self.assertNotIn('currency',sql)
        self.assertIn('within_team_pay_position',sql)


if __name__=='__main__':
    unittest.main()
