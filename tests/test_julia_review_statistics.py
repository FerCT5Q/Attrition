import sys
import unittest
from pathlib import Path
import numpy as np
from scipy import sparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import julia_review_statistics as s


class StatisticsTests(unittest.TestCase):
    def test_capacity_ties_do_not_depend_on_order(self):
        n=np.array([400,600,1000]);p=np.array([.2,.2,.1])
        w,lo,hi=s.allocate(n,p,np.ones(3,dtype=bool),.3)
        np.testing.assert_allclose(w,[.6,.6,0])
        self.assertEqual(lo@n,0);self.assertEqual(hi@n,1000)
        self.assertAlmostEqual(w@n,600)

    def test_partition_retains_small_remainder_parent(self):
        parent=np.array(['a']*650+['b']*650+['tiny']*20)
        bu=np.array(['x']*300+['y']*300+['z']*50+['x']*650+['x']*20)
        p=np.r_[np.full(650,.2),np.full(650,.1),np.full(20,.01)]
        r=s.partition(parent,bu,p,.3,100)
        self.assertEqual(len(r['labels']),3)
        self.assertEqual(np.sum(r['kinds']=='REST'),20)
        self.assertEqual(np.sum(r['kinds']=='no_priorizado'),650)

    def test_partition_valid_children_and_remainder(self):
        parent=np.array(['a']*800+['b']*800+['tiny']*20)
        bu=np.array(['x']*350+['y']*350+['z']*50+['w']*50+['x']*800+['x']*20)
        p=np.r_[np.full(800,.2),np.full(800,.1),np.full(20,.01)]
        r=s.partition(parent,bu,p,.3,100)
        self.assertNotIn('a',r['labels']);self.assertIn('b',r['labels'])
        self.assertEqual(np.sum(r['kinds']=='remanente'),100)
        self.assertEqual(np.sum(r['kinds']=='REST'),20)
        self.assertAlmostEqual(r['weights'].sum(),len(parent)*.3)

    def test_bootstrap_same_person_and_paired_identity(self):
        keys=np.tile(np.arange(60),3)
        b=s.Bootstrap(keys,500,12)
        ix=np.arange(len(keys));values=np.repeat([1.,2.,3.],60)
        estimates=b.ratio(ix,values,np.ones(len(ix)))
        np.testing.assert_allclose(estimates,2.)
        np.testing.assert_allclose(b.weights.sum(axis=1),60)
        self.assertEqual(s.interval(estimates-estimates),[0.,0.])

    def test_risk_gradient_matches_finite_differences_including_calendar(self):
        months=np.array([1,2,6,12]);x=sparse.csr_matrix(np.c_[np.ones(4),months==2,[0,1,1,0]])
        z=sparse.csr_matrix(np.c_[np.ones(4),[1,0,1,0]])
        beta=np.array([-5.,.3,.5]);q=np.array([.1,-.2]);cols=['intercept','calendar_month=2','feature=a']
        p,g=s.risk_gradient(x,z,beta,q,cols,months)
        for i in range(5):
            b1,b2=beta.copy(),beta.copy();q1,q2=q.copy(),q.copy();eps=1e-6
            if i<3:b1[i]+=eps;b2[i]-=eps
            else:q1[i-3]+=eps;q2[i-3]-=eps
            p1,_=s.risk_gradient(x,z,b1,q1,cols,months);p2,_=s.risk_gradient(x,z,b2,q2,cols,months)
            np.testing.assert_allclose(g[:,i],(p1-p2)/(2*eps),atol=1e-9)
        self.assertTrue(np.all((p>0)&(p<1)))

    def test_curvature_matches_score_derivative(self):
        eta=np.array([-7.,-3.,-1.,1.]);y=np.array([1.,0.,1.,0.]);eps=1e-5
        score,h=s.score_and_curvature(eta,y)
        plus,_=s.score_and_curvature(eta+eps,y);minus,_=s.score_and_curvature(eta-eps,y)
        np.testing.assert_allclose(h,-(plus-minus)/(2*eps),atol=1e-9)

    def test_two_stage_covariance_agrees_with_explicit_sandwich(self):
        rng=np.random.default_rng(20);n=300
        x=sparse.csr_matrix(np.c_[np.ones(n),rng.normal(size=n)])
        z=sparse.csr_matrix(np.c_[np.ones(n),rng.normal(size=n)])
        y=rng.binomial(1,.1,size=n);beta=np.array([-2.,.2]);q=np.array([.1,.1]);keys=np.arange(n)
        cov,d=s.sandwich(x,y,beta,keys,x,z,y,q,keys,2.,1.)
        self.assertTrue(d['offset_cross_derivative_included'])
        self.assertGreaterEqual(np.linalg.eigvalsh(cov).min(),-1e-10)
        # Partir cada persona en dos filas con la mitad de peso cambia la penalización,
        # pero duplicar filas Y penalización conserva exactamente el sandwich agrupado.
        xx=sparse.vstack([x,x]);zz=sparse.vstack([z,z]);yy=np.tile(y,2);kk=np.tile(keys,2)
        twice,_=s.sandwich(xx,yy,beta,kk,xx,zz,yy,q,kk,4.,2.)
        np.testing.assert_allclose(cov,twice,rtol=1e-8,atol=1e-10)


if __name__=='__main__':unittest.main()
