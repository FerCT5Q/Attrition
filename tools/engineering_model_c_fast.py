"""Compresión exacta de filas repetidas de diseño, sin cambiar búsqueda ni likelihood."""
from pathlib import Path
import json
import hashlib
import shutil
import time
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits
import engineering_model_c as base

_matrix=None
_cache={}
_fit_cache={}
_fingerprint=None
STATS={'executed_fits':0,'cache_hits':0,'compressions':[]}


def collapse(x,y):
    if not np.all(x.data==1):
        raise ValueError('Compresión sólo válida para diseño binario.')
    dense=x.astype(np.uint8).toarray()
    packed=np.packbits(dense,axis=1)
    del dense
    keys=packed.view(np.dtype((np.void,packed.shape[1]))).ravel()
    _,first,inverse=np.unique(keys,return_index=True,return_inverse=True)
    count=np.bincount(inverse).astype(float)
    successes=np.bincount(inverse,weights=np.asarray(y,float))
    return x[first].tocsr(),successes/count,count


def fit_weighted(x,y,n,l2,scale=8,max_iter=100):
    rate=np.average(y,weights=n)
    beta=np.zeros(x.shape[1]);beta[0]=np.log(-np.log1p(-np.clip(rate,1e-6,1-1e-6)))
    penalty=np.full(x.shape[1],l2*scale);penalty[0]=0
    for iteration in range(1,max_iter+1):
        eta=x@beta;exponent=np.exp(np.clip(eta,-30,5));p=base.hazard(eta)
        derivative=np.maximum(exponent*np.exp(-exponent),1e-10)
        weight=n*derivative**2/np.maximum(p*(1-p),1e-8)
        working=eta+(y-p)/derivative
        normal=(x.T@x.multiply(weight[:,None])).toarray()
        normal.flat[::normal.shape[0]+1]+=penalty
        rhs=np.asarray(x.T@(weight*working)).ravel()
        try:
            updated=np.linalg.solve(normal,rhs)
        except np.linalg.LinAlgError:
            updated=np.linalg.lstsq(normal,rhs,rcond=None)[0]
        if not np.isfinite(updated).all():
            raise RuntimeError('Coeficientes no finitos.')
        delta=np.max(np.abs(updated-beta));beta=updated
        if delta<1e-7:
            return beta,iteration
    raise RuntimeError('No convergió IRLS disperso.')


def fit_context(design,x,y,features,l2,config):
    global _matrix,_cache,_fingerprint
    if _matrix is not x:
        _matrix=x;_cache={}
        digest=hashlib.sha256()
        for arr in [x.indptr,x.indices,x.data,np.asarray(y,float)]:
            digest.update(arr.tobytes())
        digest.update(json.dumps(vars(design),sort_keys=True).encode())
        _fingerprint=digest.hexdigest()
    key=tuple(features)
    fit_key=(_fingerprint,key,l2,config['penalty_cell_scale'])
    if fit_key in _fit_cache:
        STATS['cache_hits']+=1
        beta,iterations=_fit_cache[fit_key]
        return base.Model(design,beta,features,l2,iterations)
    if key not in _cache:
        _cache[key]=collapse(x[:,design.indices(features)],y)
        STATS['compressions'].append({'rows':x.shape[0],'unique_design_rows':len(_cache[key][1]),'terms':len(features)})
    cx,cy,cn=_cache[key]
    STATS['executed_fits']+=1
    beta,iterations=fit_weighted(cx,cy,cn,l2,config['penalty_cell_scale'])
    _fit_cache[fit_key]=(beta,iterations)
    return base.Model(design,beta,features,l2,iterations)


def benchmark():
    rng=np.random.default_rng(20261008)
    unique=rng.integers(0,2,(250,18))
    unique[:,0]=1
    pattern=rng.integers(0,250,60000)
    x=sparse.csr_matrix(unique[pattern].astype(float))
    y=rng.binomial(1,.02,len(pattern))
    start=time.perf_counter();original,it=base.fit_sparse(x,y,1);original_seconds=time.perf_counter()-start
    start=time.perf_counter();cx,cy,cn=collapse(x,y);compressed,it2=fit_weighted(cx,cy,cn,1);compressed_seconds=time.perf_counter()-start
    error=float(np.max(np.abs(original-compressed)))
    if error>1e-8 or not np.allclose(x@original,x@compressed,atol=1e-8):
        raise AssertionError('La compresión cambió el ajuste.')
    return {'synthetic_rows':len(y),'unique_design_rows':len(cy),'original_seconds':original_seconds,
            'compressed_seconds':compressed_seconds,'speedup':original_seconds/compressed_seconds,
            'max_coefficient_difference':error,'iterations_original':it,'iterations_compressed':it2}


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--benchmark',action='store_true');parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        if args.benchmark:
            result=benchmark();print(json.dumps(result,indent=2))
            base.write(base.ROOT/'output/analysis/engineering/20261008/model-c-v2/performance-benchmark.json',result)
        elif args.run:
            base.CONFIG=base.ROOT/'config/engineering_model_c_20261008_fast.json'
            config=base.read(base.CONFIG)
            base.write(base.ROOT/config['output']/'frozen-optimizer.json',{
                'script':str(Path(__file__).relative_to(base.ROOT)),'sha256':base.sha(Path(__file__)),
                'method':'Agrupar filas idénticas del diseño y sumar éxitos/exposiciones; misma penalización absoluta, referencias y likelihood binomial.',
                'selection_changed':False})
            base.fit_context=fit_context
            base.run(config)
            out=base.ROOT/config['output']
            base.write(out/'optimizer-stats.json',STATS)
            result=base.read(out/'results.json')
            result['requested_hazard_fits']=result['hazard_fits']
            result['hazard_fits']=STATS['executed_fits']
            result['cached_fits']=STATS['cache_hits']
            base.write(out/'results.json',result)
        else:
            parser.error('Elegir --benchmark o --run')


if __name__=='__main__':
    main()
