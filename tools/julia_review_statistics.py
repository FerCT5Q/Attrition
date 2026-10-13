"""Estadística agregada de la revisión de Julia; las filas viven sólo en RAM."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import spearmanr


def interval(values):
    values = np.asarray(values, float)
    if not np.isfinite(values).all():
        raise ValueError('Remuestreo no finito; no se omiten réplicas silenciosamente.')
    return np.quantile(values, [.025, .975]).tolist()


def allocate(n, score, eligible, fraction):
    """Empates exactos comparten fracción; low/high incluyen todo el bloque."""
    n, score, eligible = np.asarray(n), np.asarray(score), np.asarray(eligible)
    w = np.zeros(len(n))
    remaining = n.sum()*fraction
    for value in np.unique(score[eligible])[::-1]:
        mask = eligible & (score == value)
        take = min(1., max(0., remaining/n[mask].sum()))
        w[mask] = take
        remaining -= take*n[mask].sum()
    if remaining > 1e-7 or not np.isclose(w@n, n.sum()*fraction, atol=1e-7):
        raise ValueError('La capacidad no se conserva.')
    return w, (w >= 1-1e-12).astype(float), (w > 1e-12).astype(float)


def partition(parent, bu, prediction, fraction, child_minimum=None, parent_minimum=300):
    """Partición exhaustiva por una foto; un padre o sus hijos, nunca ambos."""
    pc, names = pd.factorize(parent, sort=True)
    n = np.bincount(pc)
    means = np.bincount(pc, weights=prediction)/n
    w, _, _ = allocate(n, means, n >= parent_minimum, fraction)
    labels = np.asarray(parent, dtype=object).copy()
    kinds = np.where(n[pc] < parent_minimum, 'REST',
                     np.where(w[pc] > 0, 'padre_conservado', 'no_priorizado')).astype(object)
    if child_minimum is not None:
        for p in np.flatnonzero(w > 0):
            ix = np.flatnonzero(pc == p)
            b = np.asarray(bu, dtype=str)[ix]
            counts = pd.Series(b).value_counts()
            valid = [str(k) for k,v in counts.items() if v >= child_minimum and k not in ['(unknown)','(other)']]
            small = ~np.isin(b, valid)
            # Se exigen dos hijos BU identificables; el remanente no cuenta como uno.
            if len(valid) < 2 or (small.any() and small.sum() < child_minimum):
                continue
            labels[ix] = [str(names[p])+' | BU: '+x if x in valid else str(names[p])+' | Remanente BU' for x in b]
            kinds[ix] = np.where(small, 'remanente', 'hijo_BU')
    codes, final = pd.factorize(labels, sort=True)
    sizes = np.bincount(codes)
    scores = np.bincount(codes, weights=prediction)/sizes
    eligible = np.array([np.all(kinds[codes==i] != 'REST') for i in range(len(final))])
    exact, low, high = allocate(sizes, scores, eligible, fraction)
    assert sizes.sum() == len(parent)
    assert np.array_equal(kinds=='REST', n[pc] < parent_minimum)
    for p in np.unique(pc):
        ix = pc == p
        if len(np.unique(labels[ix])) > 1:
            assert str(names[p]) not in labels[ix]
            assert sizes[np.unique(codes[ix])].min() >= child_minimum
    return {'codes':codes,'labels':list(map(str,final)), 'kinds':kinds,
            'n':sizes,'score':scores, 'weights':exact[codes], 'low':low[codes], 'high':high[codes],
            'group_weights':exact, 'parent_weights':w[pc]}


class Bootstrap:
    """Un único remuestreo multinomial de personas para periodos y modelos."""
    def __init__(self, keys, repetitions=500, seed=20261012):
        self.codes, people = pd.factorize(keys, sort=False)
        self.people = len(people)
        rng = np.random.default_rng(seed)
        self.weights = rng.multinomial(self.people, np.full(self.people, 1/self.people), size=repetitions).astype(np.float64)
        self.repetitions = repetitions
        self.metric_cache = {}

    def sums(self, indices, cell_codes, values, cells=None):
        if cells is None: cells = int(np.max(cell_codes))+1
        matrix = sparse.coo_matrix((values,(self.codes[indices],cell_codes)), shape=(self.people,cells)).tocsr()
        return (matrix.T @ self.weights.T).T

    def ratio(self, indices, numerator, denominator):
        one = np.zeros(len(indices), dtype=int)
        a = self.sums(indices,one,numerator,1)[:,0]
        b = self.sums(indices,one,denominator,1)[:,0]
        if np.any(b <= 0): raise ValueError('Denominador bootstrap sin soporte.')
        return a/b


def loss_arrays(y,p):
    p = np.clip(p,1e-12,1-1e-12)
    return {'log_loss':-y*np.log(p)-(1-y)*np.log1p(-p),'brier':(y-p)**2}


def metrics(y,p,allocation,cells,boot,indices):
    n = len(y)
    nc = int(np.max(cells))+1
    celln = np.bincount(cells, minlength=nc)
    residual = np.bincount(cells,weights=p-y,minlength=nc)
    cw = np.divide(np.bincount(cells,weights=allocation,minlength=nc),celln,out=np.zeros(nc),where=celln>0)
    selected = float(allocation.sum())
    if selected <= 1e-12:
        return {'coverage_percent':0.,'capture_percent':0.,'suppressed':True}, {}
    values = {'risk_percent':100*p.mean(), 'observed_percent':100*y.mean(),
              'bias_pp':100*(p-y).mean(),'capture_percent':100*(allocation@y)/y.sum(),
              'group_snapshot_mae_pp':100*np.sum(cw*np.abs(residual))/selected,
              'coverage_percent':100*selected/n}
    cachekey=(id(p),int(indices[0]),len(indices))
    if cachekey in boot.metric_cache:
        cached_values,cached_replicates=boot.metric_cache[cachekey]
        values.update(cached_values)
        replicates=dict(cached_replicates)
    else:
        replicates = {}
        for k,v in loss_arrays(y,p).items():
            values[k]=float(v.mean())
            replicates[k]=boot.ratio(indices,v,np.ones(n))
        replicates['observed_percent']=100*boot.ratio(indices,y,np.ones(n))
        replicates['bias_pp']=100*boot.ratio(indices,p-y,np.ones(n))
        boot.metric_cache[cachekey]=({k:values[k] for k in ['log_loss','brier']},dict(replicates))
    replicates['capture_percent']=100*boot.ratio(indices,allocation*y,y)
    sums = boot.sums(indices,cells,p-y,nc)
    den = boot.sums(indices,np.zeros(n,dtype=int),allocation,1)[:,0]
    replicates['group_snapshot_mae_pp']=100*(np.abs(sums)@cw)/den
    return values,replicates


def score_and_curvature(eta,y):
    z=np.exp(np.clip(eta,-30,5))
    e=np.exp(-z)
    p=np.maximum(-np.expm1(-z),1e-12)
    score=y*z*e/p-(1-y)*z
    curvature=(1-y)*z+y*(z*z*e/(p*p)-z*e/p)
    return score,curvature


def sandwich(xb,yb,betab,keysb,xq,zq,yq,betaq,keysq,l2b,l2q):
    """Ecuaciones apiladas de dos etapas; incluye derivada del offset y covarianza cruzada."""
    sb,hb=score_and_curvature(np.asarray(xb@betab).ravel(),yb)
    sq,hq=score_and_curvature(np.asarray(xq@betab+zq@betaq).ravel(),yq)
    nb,nq=xb.shape[1],zq.shape[1]
    bread=np.zeros((nb+nq,nb+nq))
    bread[:nb,:nb]=(xb.T@xb.multiply(hb[:,None])).toarray()
    bread[nb:,nb:]=(zq.T@zq.multiply(hq[:,None])).toarray()
    bread[nb:,:nb]=(zq.T@xq.multiply(hq[:,None])).toarray()
    penalty=np.r_[0.,np.full(nb-1,l2b),0.,np.full(nq-1,l2q)]
    bread.flat[::len(bread)+1]+=penalty
    codes,people=pd.factorize(np.r_[keysb,keysq],sort=False)
    cb,cq=codes[:len(keysb)],codes[len(keysb):]
    ab=sparse.csr_matrix((np.ones(len(cb)),(cb,np.arange(len(cb)))),shape=(len(people),len(cb)))
    aq=sparse.csr_matrix((np.ones(len(cq)),(cq,np.arange(len(cq)))),shape=(len(people),len(cq)))
    clustered=np.hstack([(ab@xb.multiply(sb[:,None])).toarray(),(aq@zq.multiply(sq[:,None])).toarray()])
    clustered-=clustered.mean(axis=0)
    meat=clustered.T@clustered*len(people)/(len(people)-1)
    inv=np.linalg.pinv(bread,rcond=1e-11)
    cov=inv@meat@inv.T
    cov=(cov+cov.T)/2
    return cov, {'method':'Delta; sandwich de dos etapas con covarianza agrupada por persona',
                 'training_distinct_people':len(people),'parameters':nb+nq,
                 'bread_rank':int(np.linalg.matrix_rank(bread)),
                 'minimum_covariance_eigenvalue':float(np.linalg.eigvalsh(cov).min()),
                 'offset_cross_derivative_included':True,'cross_stage_covariance_included':True}


def risk_gradient(x,z,beta,betaq,columns,months):
    """Gradiente exacto del R6 con avance de calendario y recorte por mes."""
    calendar=np.zeros(13)
    colmonth={}
    for i,col in enumerate(columns):
        if col.startswith('calendar_month='):
            month=int(col.split('=')[1]);calendar[month]=beta[i];colmonth[i]=month
    fixed=np.asarray(x@beta+z@betaq).ravel()-calendar[months]
    future=(months[:,None]-1+np.arange(6))%12+1
    etas=fixed[:,None]+calendar[future]
    ex=np.exp(np.clip(etas,-30,5))
    cumulative=ex.sum(axis=1)
    deriv=ex*((etas>-30)&(etas<5))
    dc=deriv.sum(axis=1)*np.exp(-cumulative)
    gx=x.multiply(dc[:,None]).toarray()
    for col,month in colmonth.items():
        gx[:,col]+=np.exp(-cumulative)*(np.sum(deriv*(future==month),axis=1)-(months==month)*deriv.sum(axis=1))
    gz=z.multiply(dc[:,None]).toarray()
    p=-np.expm1(-cumulative)
    # clip de salida del predictor: derivada cero fuera del intervalo efectivo.
    gradients=np.hstack([gx,gz]);gradients[(p<=1e-8)|(p>=1-1e-8)]=0
    return np.clip(p,1e-8,1-1e-8),gradients


def stability(frame,p,weights,labels):
    results=[]
    dates=sorted(frame.snapshot_date.unique())
    for left,right in zip(dates,dates[1:]):
        a=np.flatnonzero(frame.snapshot_date.to_numpy()==left)
        b=np.flatnonzero(frame.snapshot_date.to_numpy()==right)
        ka=frame.person_key.iloc[a].astype(str).to_numpy();kb=frame.person_key.iloc[b].astype(str).to_numpy()
        common,ia,ib=np.intersect1d(ka,kb,return_indices=True)
        ai,bi=a[ia],b[ib]
        if len(common)<30: continue
        wa,wb=weights[ai],weights[bi]
        union=np.maximum(wa,wb).sum()
        entry=float(np.maximum(wb-wa,0).sum());exit=float(np.maximum(wa-wb,0).sum())
        results.append({'from':str(pd.Timestamp(left).date()),'to':str(pd.Timestamp(right).date()),
            'common_people':len(common),'new_people':len(b)-len(common),'departed_people':len(a)-len(common),
            'mean_absolute_risk_change_pp':float(100*np.abs(p[bi]-p[ai]).mean()),
            'common_mean_change_pp':float(100*(p[bi]-p[ai]).mean()),
            'all_population_mean_change_pp':float(100*(p[b].mean()-p[a].mean())),
            'composition_residual_pp':float(100*((p[b].mean()-p[a].mean())-(p[bi]-p[ai]).mean())),
            'rank_spearman':float(spearmanr(p[ai],p[bi]).statistic) if np.std(p[ai])*np.std(p[bi])>0 else None,
            'weighted_priority_jaccard':float(np.minimum(wa,wb).sum()/union) if union else 1.,
            'priority_entry_effective_people':entry,'priority_exit_effective_people':exit,
            'group_definition_change_percent':float(100*np.mean(labels[ai]!=labels[bi])),
            'wave_transition':bool(pd.Timestamp(left).year!=pd.Timestamp(right).year),
            'model_transition':bool(pd.Timestamp(left).year!=pd.Timestamp(right).year)})
    return results
