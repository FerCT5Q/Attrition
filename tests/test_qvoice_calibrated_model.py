"""Pruebas independientes de fórmula, fechas y persistencia; sólo datos sintéticos."""
from pathlib import Path
import json
import sys
import unittest
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import minimize

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import qvoice_calibrated_model as q
from qvoice_model_validation import fit_model


class NumericalContracts(unittest.TestCase):
    def test_offset_agrees_with_independent_likelihood_optimizer(self):
        rng=np.random.default_rng(78)
        x=np.column_stack([np.ones(5000),rng.integers(0,2,(5000,2))])
        offset=rng.normal(-3.5,.3,5000)
        y=rng.binomial(1,q.hazard(offset+x@np.array([.2,.6,-.4])))
        beta,ok,_=q.fit_offset(sparse.csr_matrix(x),y,offset,2.)
        def objective(b):
            p=-np.expm1(-np.exp(offset+x@b))
            return -(y*np.log(p)+(1-y)*np.log1p(-p)).sum()+np.sum(b[1:]**2)
        other=minimize(objective,np.zeros(3),method='BFGS',options={'gtol':1e-6})
        self.assertTrue(ok)
        np.testing.assert_allclose(beta,other.x,atol=2e-5)

    def test_six_month_product_and_artifact_roundtrip(self):
        from critical_tech_discrete_hazard_model import six_month_predictions
        rng=np.random.default_rng(8)
        n=1200
        frame=pd.DataFrame({'snapshot_date':pd.date_range('2025-01-01',periods=n,freq='h'),
            'level_grouped':rng.choice(['L1','L2'],n),'tenure_playbook_band':rng.choice(['A','B'],n),
            'manager_changes_12m':rng.choice(['0','1'],n),'qv_Q4':rng.choice(['v0','v1'],n),
            'exposure_count':1,'event_count':rng.binomial(1,.08,n)})
        base=fit_model(frame,['level_grouped','tenure_playbook_band','manager_changes_12m','calendar_month'],1.)
        np.testing.assert_allclose(q.six_month_risk(base,frame,np.zeros(n)),six_month_predictions(base,frame),atol=1e-12)
        enc=q.CategoryEncoder.fit(frame,['qv_Q4'])
        beta=np.array([.1,.4])
        cal={'intercept':.2,'slope':.8}
        artifact={'base':q.export_base(base),'correction':{'kind':'blocks','encoder':q.asdict(enc),'beta':beta.tolist()},'calibration':cal}
        actual=q.predict_artifact(json.loads(json.dumps(artifact)),frame)
        expected=q.six_month_risk(base,frame,enc.transform(frame)@beta,cal)
        np.testing.assert_allclose(actual,expected,atol=1e-12)
        pieces=[]
        for m in range(6):
            future=frame.copy()
            future['snapshot_date']=frame.snapshot_date+pd.DateOffset(months=m)
            pieces.append(q.hazard(cal['intercept']+cal['slope']*(q.base_eta(base,future)+enc.transform(frame)@beta)))
        np.testing.assert_allclose(actual,1-np.prod(1-np.column_stack(pieces),axis=1),atol=1e-12)

    def test_temporal_splits_exclude_labels_after_cutoff(self):
        dates=pd.date_range('2024-01-01','2026-02-01',freq='MS')
        f=pd.DataFrame({'snapshot_date':dates,'label_end':dates+pd.offsets.MonthBegin(1)})
        core,selection,calibration,final,eligible=q.split_months(f,'2026-01-01')
        self.assertLessEqual(core.label_end.max(),selection.snapshot_date.min())
        self.assertLessEqual(final.label_end.max(),calibration.snapshot_date.min())
        self.assertLessEqual(calibration.label_end.max(),pd.Timestamp('2026-01-01'))
        self.assertEqual(len(selection),2)
        self.assertEqual(len(calibration),2)
        self.assertTrue(set(selection.index).isdisjoint(calibration.index))

    def test_calibration_keeps_monotonic_hazard(self):
        rng=np.random.default_rng(981)
        eta=rng.normal(-3.,.7,20000)
        y=rng.binomial(1,q.hazard(.5+.9*eta))
        c=q.calibrate(eta,y)
        self.assertGreater(c['slope'],0)
        fitted=c['intercept']+c['slope']*eta
        # Cloglog no es el enlace canónico: el score del intercepto pondera residuos.
        z=np.exp(fitted)
        score=((1-y)*z-y*z/np.expm1(z)).sum()
        self.assertLess(abs(score),1e-3)
        self.assertLess(q.negative_log_likelihood(fitted,y),q.negative_log_likelihood(eta,y))
        ordered=np.sort(eta)
        self.assertTrue(np.all(np.diff(q.hazard(c['intercept']+c['slope']*ordered))>=0))

    def test_pca_parameters_stay_frozen_and_missing_is_explicit(self):
        train=pd.DataFrame({'qv_M01':['v0','v1','missing','v1'],'qv_M02':['v1','v0','v1','v0']})
        enc=q.PCAEncoder.fit(train,list(train.columns),1)
        means=enc.means.copy()
        transformed=enc.transform(pd.DataFrame({'qv_M01':['missing'],'qv_M02':['v0']})).toarray()
        np.testing.assert_array_equal(enc.means,means)
        self.assertEqual(transformed[0,-2],1)
        self.assertTrue(np.isfinite(transformed).all())


if __name__=='__main__':
    unittest.main()
