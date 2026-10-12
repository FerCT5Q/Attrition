"""Verificación sintética solicitada para C; no accede a datos de personas."""
import sys
import unittest
from pathlib import Path
from copy import deepcopy
import numpy as np
import pandas as pd
from scipy import sparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import engineering_model_c as c


class ModelCTests(unittest.TestCase):
    def setUp(self):
        self.config=c.read(c.CONFIG)
        rng=np.random.default_rng(44)
        n=1200
        self.frame=pd.DataFrame({'snapshot_date':np.tile(pd.to_datetime(['2023-10-22','2023-11-26','2023-12-31']),n//3),
                                 'a':rng.choice(['bajo','alto'],n),'b':rng.choice(['x','y','z'],n)})
        self.frame['calendar_month']=self.frame.snapshot_date.dt.month.astype(str)
        self.frame['y_next']=rng.binomial(1,np.where(self.frame.a=='alto',.07,.02))
        self.features=['a','b','calendar_month','a_b']
        self.interactions={'a_b':['a','b']}

    def design(self):
        return c.Design.fit(self.frame,self.features,self.interactions)

    def test_sparse_reference_matrix(self):
        d=self.design();x=d.matrix(self.frame).toarray();values=d.prepare(self.frame,d.references,d.interactions)
        expected=np.column_stack([np.ones(len(self.frame))]+[(values[n.split('=',1)[0]]==n.split('=',1)[1]).astype(float) for n in d.columns[1:]])
        np.testing.assert_array_equal(x,expected)

    def test_unknown_is_reference_without_refitting(self):
        d=self.design();f=self.frame.iloc[:1].copy();f['a']='futuro'
        columns=[i for i,n in enumerate(d.columns) if n.startswith('a=')]
        self.assertEqual(d.matrix(f).toarray()[0,columns].sum(),0)
        self.assertNotIn('futuro',d.levels['a'])

    def test_sparse_irls_agrees_with_dense_historical(self):
        import critical_tech_discrete_hazard_model as hz
        d=self.design();x=d.matrix(self.frame);y=self.frame.y_next.to_numpy()
        beta,_=c.fit_sparse(x,y,1)
        class Encoder:
            def transform(self,frame):
                return x.toarray()
        f=self.frame.assign(exposure_count=1,event_count=y)
        original=hz.fit_irls
        # qvoice_model_validation aplica el wrapper histórico l2*8 al importar.
        m=original(f,'cloglog',1,Encoder())
        self.assertTrue(m.converged)
        np.testing.assert_allclose(beta,m.beta,atol=1e-8)

    def test_six_month_formula_matches_monthly_product(self):
        d=self.design();x=d.matrix(self.frame);beta,_=c.fit_sparse(x,self.frame.y_next,1)
        model=c.Model(d,beta,self.features,1,1)
        survival=np.ones(len(self.frame))
        for j in range(6):
            f=self.frame.copy();f['calendar_month']=((f.snapshot_date.dt.month-1+j)%12+1).astype(str)
            survival*=1-c.hazard(d.matrix(f)@beta)
        np.testing.assert_allclose(model.risk(self.frame),1-survival,atol=1e-10)

    def test_roundtrip_minimal_artifact(self):
        d=self.design();x=d.matrix(self.frame);features=['a','calendar_month'];idx=d.indices(features)
        beta,_=c.fit_sparse(x[:,idx],self.frame.y_next,1)
        model=c.Model(d,beta,features,1,1);a=model.artifact()
        restored=c.Model(c.Design(**a['encoder']),np.asarray(a['beta']),a['features'],a['l2'],a['iterations'])
        minimal=self.frame[['snapshot_date','a','calendar_month']]
        np.testing.assert_allclose(restored.risk(minimal),model.risk(self.frame),atol=1e-12)

    def test_monthly_label_boundary(self):
        f=self.frame.iloc[:3].copy();f['label_end']=pd.to_datetime(['2023-11-26','2023-12-31','2024-01-28'])
        train=c.train_before(f,'2023-12-01')
        self.assertEqual(len(train),1)
        self.assertLessEqual(train.label_end.max(),pd.Timestamp('2023-12-01'))

    def test_r6_immature_is_excluded(self):
        f=self.frame.copy();f['r6_end']=f.snapshot_date+pd.DateOffset(months=6);f['y_6m']=0
        with self.assertRaises(RuntimeError):
            c.evaluation(f,'2023-10-01',3,'2024-05-01')
        result=c.evaluation(f,'2023-10-01',1,'2024-05-01')
        self.assertTrue((result.r6_end<=pd.Timestamp('2024-05-01')).all())

    def test_screening_preserves_hierarchy(self):
        d=self.design();x=d.matrix(self.frame);settings=deepcopy(self.config)
        settings.update({'base_features':['a'],'candidate_features':self.features,'interactions':self.interactions,'screening_inverse_penalties':[.1,1]})
        sets,_=c.screen(d,x,self.frame.y_next,settings)
        for features in sets:
            if 'a_b' in features:
                self.assertTrue({'a','b'}<=set(features))

    def test_constant_intercept_model(self):
        x=sparse.csr_matrix(np.ones((1000,1)));y=np.r_[np.ones(30),np.zeros(970)]
        beta,_=c.fit_sparse(x,y,1)
        self.assertAlmostEqual(float(c.hazard(beta)[0]),.03,places=10)

    def test_loss_sign(self):
        y=np.array([0,0,1,1]);good=np.array([.1,.1,.9,.9]);bad=np.repeat(.5,4)
        for k in c.losses(y,good):
            self.assertLess(c.losses(y,good)[k].mean(),c.losses(y,bad)[k].mean())

    def test_sql_temporal_and_privacy_guards(self):
        sql=(c.ROOT/self.config['query']).read_text(encoding='utf-8')
        c.db.validate_readonly(sql)
        self.assertIn('__RUN_SALT__',sql)
        self.assertIn('f.next_snapshot_date IS NULL',sql)
        self.assertIn('x.known_date <= p.snapshot_date',sql)
        self.assertIn('r.known_date <= p.snapshot_date',sql)
        self.assertIn('h.row_date <= p.snapshot_date',sql)
        self.assertIn('h.transfer_date > DATEADD(month, -12, p.snapshot_date)',sql)
        final_select=sql[sql.index('SELECT\n  f.snapshot_date,'):]
        self.assertNotIn('f.cr AS',final_select)
        self.assertNotIn(' AS employee_id',final_select)
        self.assertNotIn('qvoice',c.db.strip_comments(sql).lower())

    def test_no_qvoice_candidate(self):
        self.assertFalse(self.config['qvoice_included'])
        self.assertFalse(any(f.startswith('qv_') for f in self.config['candidate_features']))
        self.assertEqual(len(self.config['candidate_features']),21)

    def test_readonly_helper_blocks_writes_and_wildcards(self):
        for sql in ['DELETE FROM hrda.example','SELECT * FROM hrda.example','SELECT 1; SELECT 2']:
            with self.assertRaises(ValueError):
                c.db.validate_readonly(sql)
        self.assertEqual(c.db.validate_readonly('SELECT COUNT(*) AS n FROM hrda.example'),'SELECT COUNT(*) AS n FROM hrda.example')

    def test_groups_do_not_require_future_outcomes(self):
        d=self.design();x=d.matrix(self.frame);beta,_=c.fit_sparse(x,self.frame.y_next,1)
        model=c.Model(d,beta,self.features,1,1);settings=deepcopy(self.config)
        settings['interactions']=self.interactions
        _,_,groups=c.make_groups(model,self.frame.drop(columns=['y_next']),settings)
        self.assertLessEqual(len(groups['rules']),8)
        self.assertTrue(all(len(r['conditions'])<=3 for r in groups['rules']))
        self.assertEqual(groups['training_snapshot'],'2023-12-31')

    def test_transfer_history_is_not_implicitly_no_event(self):
        sql=(c.ROOT/self.config['query']).read_text(encoding='utf-8')
        self.assertIn("f.snapshot_date < DATE '2023-10-23' THEN '(historia no confirmada)'",sql)

    def test_exact_compression_preserves_fit_and_likelihood(self):
        import engineering_model_c_fast as fast
        d=self.design();x=d.matrix(self.frame);y=self.frame.y_next.to_numpy(float)
        beta,_=c.fit_sparse(x,y,1)
        cx,cy,cn=fast.collapse(x,y);compressed,_=fast.fit_weighted(cx,cy,cn,1)
        self.assertEqual(cn.sum(),len(y))
        self.assertAlmostEqual(float((cn*cy).sum()),float(y.sum()),places=9)
        np.testing.assert_allclose(compressed,beta,atol=1e-8)
        p=c.hazard(cx@compressed)
        expanded_loss=float(c.losses(y,c.hazard(x@beta))['log_loss'].sum())
        compressed_loss=float((-cn*cy*np.log(p)-cn*(1-cy)*np.log1p(-p)).sum())
        self.assertAlmostEqual(expanded_loss,compressed_loss,places=7)

    def test_compression_rejects_nonbinary_design(self):
        import engineering_model_c_fast as fast
        with self.assertRaises(ValueError):
            fast.collapse(sparse.csr_matrix([[1.,.4],[1.,0.]]),np.array([0.,1.]))


if __name__=='__main__':
    unittest.main()
