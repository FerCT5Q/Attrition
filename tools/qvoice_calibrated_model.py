"""Modelo B + QVoice: 255 subconjuntos, PCA y calibración con meses reservados.

Sólo parámetros y agregados se guardan. Ningún frame o score individual se exporta.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
from pathlib import Path
import secrets
import sys
import time

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import minimize
from threadpoolctl import threadpool_limits

from qvoice_model_data import ROOT, load_config, sha256_file, utc_now, write_json
from qvoice_model_experiment import read_model_frame, attach_qvoice, modeling_frames
from qvoice_model_validation import (fit_model, add_interactions, INTERACTIONS,
    frame_metrics, period_frame, bootstrap_paired, decision)


def log(message):
    print(f'[{time.strftime("%H:%M:%S")}] {message}', flush=True)


def hazard(eta):
    return -np.expm1(-np.exp(np.clip(eta, -30, 5)))


def negative_log_likelihood(eta, y):
    z = np.exp(np.clip(eta, -30, 5))
    return float(np.sum((1-y)*z-y*np.log(-np.expm1(-z))))


def fit_offset(x, y, offset, l2, max_iter=80):
    """IRLS binomial cloglog con offset; búsqueda de paso decreciente y ridge."""
    x = sparse.csr_matrix(x, dtype=float)
    y, offset = np.asarray(y, float), np.asarray(offset, float)
    penalty = np.full(x.shape[1], float(l2))
    penalty[0] = 0
    beta = np.zeros(x.shape[1])
    previous = negative_log_likelihood(offset, y)
    for iteration in range(max_iter):
        eta = offset+x@beta
        z = np.exp(np.clip(eta, -30, 5))
        p = np.clip(-np.expm1(-z), 1e-12, 1-1e-12)
        d = np.maximum(z*np.exp(-z), 1e-12)
        w = d*d/np.maximum(p*(1-p), 1e-12)
        target = x@beta+(y-p)/d
        normal = (x.T @ x.multiply(w[:,None])).toarray()
        normal.flat[::len(beta)+1] += penalty + 1e-10
        rhs = np.asarray(x.T@(w*target)).ravel()
        proposed = np.linalg.solve(normal, rhs)
        direction = proposed-beta
        step = 1.0
        for _ in range(24):
            trial = beta+step*direction
            value = negative_log_likelihood(offset+x@trial, y)+0.5*np.sum(penalty*trial**2)
            if value <= previous+1e-8:
                break
            step *= 0.5
        else:
            return beta, False, iteration+1
        delta = np.max(np.abs(trial-beta))
        beta, previous = trial, value
        if delta < 1e-7:
            return beta, True, iteration+1
    return beta, False, max_iter


@dataclass
class CategoryEncoder:
    features: list[str]
    levels: dict[str,list[str]]
    references: dict[str,str]
    columns: list[str]

    @classmethod
    def fit(cls, frame, features):
        levels, refs, columns = {}, {}, ['intercept']
        for name in features:
            values = frame[name].astype(str)
            counts = values.value_counts()
            refs[name] = str(counts.index[0])
            levels[name] = sorted(counts.index.astype(str))
            columns += [f'{name}={v}' for v in levels[name] if v != refs[name]]
        return cls(list(features), levels, refs, columns)

    def transform(self, frame):
        blocks = [sparse.csr_matrix(np.ones((len(frame),1)))]
        for name in self.features:
            values = frame[name].astype(str).to_numpy()
            cats = [v for v in self.levels[name] if v != self.references[name]]
            blocks.extend(sparse.csr_matrix((values == v).astype(float)[:,None]) for v in cats)
        return sparse.hstack(blocks, format='csr')

    def indices(self, features):
        names = set(features)
        return [i for i,c in enumerate(self.columns) if i==0 or c.split('=',1)[0] in names]


@dataclass
class PCAEncoder:
    features: list[str]
    means: np.ndarray
    scales: np.ndarray
    vectors: np.ndarray
    explained_variance_ratio: np.ndarray
    components: int

    @staticmethod
    def raw(frame, features):
        return np.column_stack([frame[c].astype(str).map({'v0':0.,'v1':1.}).to_numpy() for c in features])

    @classmethod
    def fit(cls, frame, features, components=10):
        # Cada persona-wave cuenta una vez en PCA; no se sobrepondera por meses repetidos.
        basis = frame.drop_duplicates(['person_key','qvoice_wave']) if 'person_key' in frame else frame
        values = cls.raw(basis, features)
        means = np.nanmean(values,axis=0)
        if not np.isfinite(means).all():
            raise ValueError('PCA: falta una pregunta en entrenamiento.')
        scales = np.sqrt(np.maximum(means*(1-means),1e-6))
        z = (np.where(np.isfinite(values),values,means)-means)/scales
        covariance = z.T@z/max(len(z)-1,1)
        eig, vec = np.linalg.eigh(covariance)
        order = np.argsort(eig)[::-1]
        eig, vec = eig[order], vec[:,order]
        # Fija el signo de cada vector para reproducibilidad.
        for c in range(vec.shape[1]):
            if vec[np.argmax(np.abs(vec[:,c])),c] < 0:
                vec[:,c] *= -1
        return cls(list(features),means,scales,vec,eig/eig.sum(),components)

    def transform(self, frame):
        raw = self.raw(frame,self.features)
        missing = ~np.isfinite(raw)
        z = (np.where(missing,self.means,raw)-self.means)/self.scales
        return sparse.csr_matrix(np.column_stack([np.ones(len(frame)),z@self.vectors[:,:self.components],missing.astype(float)]))

    def export(self):
        return {k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in asdict(self).items()}


def split_months(frame, cutoff, selection_count=2, calibration_count=2):
    cutoff = pd.Timestamp(cutoff)
    eligible = frame.loc[frame.label_end <= cutoff].copy()
    dates = sorted(eligible.snapshot_date.unique())
    if len(dates) <= selection_count+calibration_count:
        raise ValueError('Historia insuficiente para los tres tramos temporales.')
    cal_dates = dates[-calibration_count:]
    select_dates = dates[-calibration_count-selection_count:-calibration_count]
    core = eligible.loc[eligible.label_end <= pd.Timestamp(select_dates[0])].copy()
    selection = eligible.loc[eligible.snapshot_date.isin(select_dates)].copy()
    calibration = eligible.loc[eligible.snapshot_date.isin(cal_dates)].copy()
    final = eligible.loc[eligible.label_end <= pd.Timestamp(cal_dates[0])].copy()
    if core.empty or core.label_end.max()>selection.snapshot_date.min() or final.label_end.max()>calibration.snapshot_date.min():
        raise ValueError('Solapamiento temporal entre ajuste, selección o calibración.')
    return core, selection, calibration, final, eligible


def base_eta(model, frame):
    raw = set(model.fitted.encoder.features)-set(INTERACTIONS)-{'calendar_month'}
    raw |= {field for pair in INTERACTIONS.values() for field in pair}
    prepared = add_interactions(frame[['snapshot_date']+sorted(raw)],model.references)
    return model.fitted.encoder.transform(prepared) @ model.fitted.beta


def calibrate(eta, y, slope_l2=10., bounds=(0.25,4.)):
    """Ajusta sólo en el tramo reservado; pendiente positiva para preservar el orden mensual."""
    eta,y=np.asarray(eta,float),np.asarray(y,float)
    center=float(np.mean(eta))
    centered=eta-center
    def objective(theta):
        a,b=theta
        linear=a+b*centered
        z=np.exp(np.clip(linear,-30,5))
        gradient=(1-y)*z-y*z/np.expm1(z)
        loss=negative_log_likelihood(linear,y)+0.5*slope_l2*(b-1)**2
        return loss,np.array([gradient.sum(),gradient@centered+slope_l2*(b-1)])
    result=minimize(objective,[center,1.],jac=True,method='L-BFGS-B',bounds=[(-15,5),bounds],options={'ftol':1e-12,'gtol':1e-7,'maxiter':300})
    if not result.success:
        raise ValueError('No convergió la calibración temporal.')
    return {'intercept':float(result.x[0]-result.x[1]*center),'slope':float(result.x[1]),'slope_l2':slope_l2,'converged':True}


def six_month_risk(model, frame, correction, calibration=None):
    a,b=(0.,1.) if calibration is None else (calibration['intercept'],calibration['slope'])
    calendar=np.zeros(13)
    for col,coef in zip(model.fitted.encoder.columns,model.fitted.beta):
        if col.startswith('calendar_month='):
            calendar[int(col.split('=')[1])]=coef
    month=frame.snapshot_date.dt.month.to_numpy()
    fixed=base_eta(model,frame)-calendar[month]+correction
    future=(month[:,None]-1+np.arange(6))%12+1
    cumulative=np.exp(np.clip(a+b*fixed,-30,5))*np.sum(np.exp(b*calendar[future]),axis=1)
    return np.clip(-np.expm1(-cumulative),1e-8,1-1e-8)


def survey_training(frame):
    result=frame.loc[frame.qvoice_wave.astype(str) != 'ninguna'].copy()
    if len(result)<30 or result.event_count.sum()<30:
        raise ValueError('Historia QVoice insuficiente para estimar una corrección.')
    return result


def fit_b(frame, config, l2=10.):
    model=fit_model(frame,config['control']['features'],l2,config['control']['penalty_cell_scale'])
    if not model.fitted.converged:
        raise ValueError('B no converge con la penalización declarada.')
    return model


def correlation_summary(frame, features):
    basis=frame.drop_duplicates(['person_key','qvoice_wave'])
    raw=PCAEncoder.raw(basis,features)
    rows=[]
    for i,j in itertools.combinations(range(len(features)),2):
        valid=np.isfinite(raw[:,i]) & np.isfinite(raw[:,j])
        if valid.sum()<30:
            continue
        a,b=raw[valid,i],raw[valid,j]
        if np.std(a)==0 or np.std(b)==0:
            continue
        rows.append({'left':features[i],'right':features[j],'pairs':int(valid.sum()),'correlation':float(np.corrcoef(a,b)[0,1])})
    return sorted(rows,key=lambda r:-abs(r['correlation']))


def search(core, selection, config, destination):
    log('Ajustando B del tramo de selección...')
    base=fit_b(core,config)
    train=survey_training(core)
    blocks=config['search']['blocks']
    features=list(dict.fromkeys(c for block in blocks.values() for c in block))
    valid_states=['v0','v1','<50','50–69','70–79','80–89','90–99','100']
    for name in features+config['search']['pca_items']:
        if any(int(part[name].astype(str).isin(valid_states).sum())<30 for part in (train,selection)):
            raise ValueError(f'{name} carece de cobertura mínima en ajuste o selección.')
    encoder=CategoryEncoder.fit(train,features)
    x=encoder.transform(train)
    xv=encoder.transform(selection)
    offset=base_eta(base,train)
    offsetv=base_eta(base,selection)
    y=train.event_count.to_numpy(float)
    yv=selection.event_count.to_numpy(float)
    trials=[]
    names=list(blocks)
    for mask in range(1,1<<len(names)):
        selected=[name for i,name in enumerate(names) if mask&(1<<i)]
        columns=list(dict.fromkeys(c for name in selected for c in blocks[name]))
        indices=encoder.indices(columns)
        tx,vx=x[:,indices],xv[:,indices]
        for l2 in config['search']['l2_grid']:
            beta,converged,iterations=fit_offset(tx,y,offset,l2)
            score=float(np.mean((yv-hazard(offsetv+vx@beta))**2)) if converged else None
            trials.append({'id':'+'.join(selected),'kind':'blocks','blocks':selected,'features':columns,'l2':l2,'parameters':len(beta),'converged':bool(converged),'iterations':iterations,'monthly_brier':score})
        if mask%16==0 or mask==(1<<len(names))-1:
            log(f'Subconjuntos terminados: {mask}/255.')
            write_json(destination/'selection-progress.json',{'completed_subsets':mask,'trials':trials,'created_at':utc_now()})
    pca=PCAEncoder.fit(train,config['search']['pca_items'])
    for k in config['search']['pca_components']:
        pca.components=k
        tx,vx=pca.transform(train),pca.transform(selection)
        for l2 in config['search']['l2_grid']:
            beta,converged,iterations=fit_offset(tx,y,offset,l2)
            score=float(np.mean((yv-hazard(offsetv+vx@beta))**2)) if converged else None
            trials.append({'id':f'pca_{k}','kind':'pca','components':k,'features':pca.features,'l2':l2,'parameters':len(beta),'converged':bool(converged),'iterations':iterations,'monthly_brier':score})
    eligible=[r for r in trials if r['converged'] and r['monthly_brier'] is not None]
    if not eligible:
        raise ValueError('Ningún candidato convergió.')
    winner=min(eligible,key=lambda r:(r['monthly_brier'],r['parameters'],r['l2'],r['id']))
    output={'selected':winner,'trials':trials,'baseline_monthly_brier':float(np.mean((yv-hazard(offsetv))**2)),
            'scope':'Ajuste de la corrección con B como offset fijo; búsqueda sólo en los meses de selección.',
            'pca_explained_variance_ratio':pca.explained_variance_ratio.tolist(),
            'correlations':correlation_summary(train,config['search']['pca_items']),
            'maximum_training_label_end':str(core.label_end.max().date()),
            'selection_dates':[str(pd.Timestamp(d).date()) for d in sorted(selection.snapshot_date.unique())]}
    write_json(destination/'selection.json',output)
    log(f'Selección: {winner["id"]}, L2={winner["l2"]}; Brier mensual={winner["monthly_brier"]:.7f}.')
    return winner


def export_base(model):
    encoder=asdict(model.fitted.encoder)
    encoder['time_origin']=str(encoder['time_origin'].date())
    return {'beta':model.fitted.beta.tolist(),'l2':model.fitted.l2,'encoder':encoder,'interaction_references':model.references,'link':'cloglog'}


def predict_artifact(artifact, frame):
    """Predicción sólo en memoria a partir del JSON, sin acceso a etiquetas futuras."""
    from critical_tech_discrete_hazard_model import IRLSModel
    from engineering_hazard_adjustment import TrendEncoder
    from qvoice_model_validation import FrozenModel
    base_data=artifact['base']
    enc_data=dict(base_data['encoder'])
    enc_data['time_origin']=pd.Timestamp(enc_data['time_origin'])
    base=FrozenModel(IRLSModel('cloglog',base_data['l2'],np.array(base_data['beta']),TrendEncoder(**enc_data),0,True),base_data['interaction_references'])
    correction=artifact['correction']
    qdata=dict(correction['encoder'])
    if correction['kind']=='pca':
        for name in ('means','scales','vectors','explained_variance_ratio'):
            qdata[name]=np.array(qdata[name])
        qencoder=PCAEncoder(**qdata)
    else:
        qencoder=CategoryEncoder(**qdata)
    residual=np.asarray(qencoder.transform(frame)@np.array(correction['beta']))
    return six_month_risk(base,frame,residual,artifact['calibration'])


def fit_final(final, calibration_frame, winner, config):
    base=fit_b(final,config)
    train=survey_training(final)
    encoder=(CategoryEncoder.fit(train,winner['features']) if winner['kind']=='blocks'
             else PCAEncoder.fit(train,winner['features'],winner['components']))
    beta,converged,iterations=fit_offset(encoder.transform(train),train.event_count.to_numpy(float),base_eta(base,train),winner['l2'])
    if not converged:
        raise ValueError('No convergió la corrección seleccionada en el reajuste final.')
    cal_eta=base_eta(base,calibration_frame)
    cal_y=calibration_frame.event_count.to_numpy(float)
    policy=config['search']['calibration']
    cal=calibrate(cal_eta+encoder.transform(calibration_frame)@beta,cal_y,policy['slope_l2'],tuple(policy['slope_bounds']))
    base_cal=calibrate(cal_eta,cal_y,policy['slope_l2'],tuple(policy['slope_bounds']))
    av_features=[f'av_{c}' for c in winner['features']]
    av_encoder=CategoryEncoder.fit(train,av_features)
    av_beta,av_ok,_=fit_offset(av_encoder.transform(train),train.event_count.to_numpy(float),base_eta(base,train),winner['l2'])
    if not av_ok:
        raise ValueError('No convergió el control de disponibilidad.')
    av_cal=calibrate(cal_eta+av_encoder.transform(calibration_frame)@av_beta,cal_y,policy['slope_l2'],tuple(policy['slope_bounds']))
    artifact={
        'schema_version':1,'name':'B + QVoice calibrado','status':'experimental',
        'architecture':'cloglog con B como offset fijo, corrección QVoice y calibración temporal',
        'selected':winner,'base':export_base(base),'correction':{'encoder':asdict(encoder) if isinstance(encoder,CategoryEncoder) else encoder.export(),'kind':winner['kind'],'beta':beta.tolist(),'l2':winner['l2'],'converged':converged,'iterations':iterations},
        'calibration':cal,'base_only_calibration':base_cal,
        'maximum_fit_label_end':str(final.label_end.max().date()),
        'calibration_snapshots':[str(pd.Timestamp(d).date()) for d in sorted(calibration_frame.snapshot_date.unique())],
        'maximum_calibration_label_end':str(calibration_frame.label_end.max().date()),
        'temporal_policy':config['temporal_policy_reference'],'privacy':config['privacy'],
        'authorization':config['authorization'],'created_at':utc_now(),
        'forecast_rule':'Calendario futuro conocido; otras covariables congeladas; 1-producto(1-h_m).'}
    return base,encoder,beta,cal,base_cal,av_encoder,av_beta,av_cal,artifact


def run(config, root):
    for c in config['candidates']:
        ref=json.loads((root/'variables'/c['id']/'assessment-reference.json').read_text(encoding='utf-8'))
        if sha256_file(ROOT/ref['path']/'manifest.json') != ref['manifest_sha256']:
            raise ValueError('Cambió un assessment de origen.')
    metadata=json.loads((root/'preflight/source-metadata.json').read_text(encoding='utf-8'))
    contract={'configuration_sha256':hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
              'implementation_sha256':sha256_file(Path(__file__)),
              'sources':{w['file']:w['sha256'] for w in metadata['waves']}}
    contract_path=root/'execution-contract.json'
    if contract_path.exists():
        if json.loads(contract_path.read_text(encoding='utf-8')) != contract:
            raise ValueError('La reanudación requiere el mismo código, configuración y fuentes; abra otra ejecución.')
    else:
        write_json(contract_path,contract)
    log('Cargando el frame autorizado en memoria...')
    salt=secrets.token_hex(32)
    frame=read_model_frame(config,salt)
    log('Enlazando columnas QVoice de las dos waves utilizables...')
    frame=attach_qvoice(frame,config,metadata,salt)
    del salt
    monthly,direct=modeling_frames(frame)
    del frame
    # Auditorías por snapshot; la salida nunca contiene llaves individuales.
    audit=[]
    for when,group in monthly.groupby('snapshot_date',sort=True):
        item={'snapshot_date':str(when.date()),'people':int(group.person_key.nunique()),'rows':len(group)}
        item['available']={c:int(group[c].astype(str).isin(['v0','v1','<50','50–69','70–79','80–89','90–99','100']).sum()) for c in list(dict.fromkeys(v for b in config['search']['blocks'].values() for v in b))}
        audit.append(item)
    write_json(root/'monthly-coverage.json',{'reporting_mode':'presentation','rows':audit,'query':config['paths']['model_query'],'created_at':utc_now(),'score_effect':'No se asignan nuevos scores con esta auditoría del modelo.'})
    previous=json.loads((ROOT/'output/analysis/engineering/20261008/qvoice-model-b-annual-lag-v2/comparison-results.json').read_text(encoding='utf-8'))
    previous_periods={p['period']:p for p in previous['variants'][0]['periods'] if p['main']}
    periods=[]
    for period in config['validation']['main_periods']:
        directory=root/'folds'/period['id']
        if (directory/'evaluation.json').is_file():
            log(f'Reutilizando el periodo completo {period["id"]} de esta misma ejecución.')
            periods.append(json.loads((directory/'evaluation.json').read_text(encoding='utf-8')))
            continue
        directory.mkdir(parents=True,exist_ok=True)
        log(f'Periodo {period["id"]}: selección interna y calibración.')
        core,selection,calibration,final,eligible=split_months(monthly,period['start'],config['search']['selection_intervals'],config['search']['calibration_intervals'])
        winner=(json.loads((directory/'selection.json').read_text(encoding='utf-8'))['selected']
                if (directory/'selection.json').is_file() else search(core,selection,config,directory))
        base,encoder,beta,cal,base_cal,av_encoder,av_beta,av_cal,artifact=fit_final(final,calibration,winner,config)
        write_json(directory/'model.json',artifact)
        test=period_frame(direct,period,config['knowledge_boundary'])
        if test.snapshot_date.nunique()!=period['expected_snapshots'] or test.person_key.nunique()<30 or test.loc[test.event_count>0,'person_key'].nunique()<30:
            raise ValueError('El periodo no cumple seguimiento o privacidad.')
        # B de referencia se ajusta con toda la historia admitida y el L2 seleccionado en su comparación anterior.
        control=fit_b(eligible,config,previous_periods[period['id']]['control']['l2'])
        correction=np.asarray(encoder.transform(test)@beta)
        predictions={
            'control':six_month_risk(control,test,np.zeros(len(test))),
            'base_calibrated':six_month_risk(base,test,np.zeros(len(test)),base_cal),
            'availability':six_month_risk(base,test,np.asarray(av_encoder.transform(test)@av_beta),av_cal),
            'uncalibrated':six_month_risk(base,test,correction),
            'response':six_month_risk(base,test,correction,cal)}
        metrics={name:frame_metrics(test,p) for name,p in predictions.items()}
        row={'period':period['id'],'main':True,'complete':True,'status':'evaluated','snapshot_count':test.snapshot_date.nunique(),'people':test.person_key.nunique(),'first_snapshot':str(test.snapshot_date.min().date()),'last_snapshot':str(test.snapshot_date.max().date()),'selected':winner,'calibration':cal,'cohort_equality_verified':True,**metrics}
        row['control_reconciliation']={key:float(metrics['control'][key]-previous_periods[period['id']]['control'][key]) for key in ('exposures','event_exposures','pr_auc','lift_at_10_percent','brier_score')}
        valid=test[[f'av_{c}' for c in winner['features']]].astype(str).eq('available').all(axis=1)
        row['response_complete_coverage_percent']=100*float(valid.mean())
        write_json(directory/'metrics.json',row)
        log(f'{period["id"]}: bootstrap pareado de los cinco modelos...')
        row['uncertainty']=bootstrap_paired(test.person_key.to_numpy(),test.event_count.to_numpy(float),predictions,config['validation']['bootstrap_repetitions'],config['validation']['bootstrap_seed'],config['validation']['confidence_level'])
        write_json(directory/'evaluation.json',row)
        periods.append(row)
        del core,selection,calibration,final,eligible,test,predictions
    summary={'experiment':config['experiment_id'],'created_at':utc_now(),'reporting_mode':'presentation','knowledge_boundary':config['knowledge_boundary'],'periods':periods,'decision':decision(periods),'evaluation_caveat':config['search']['evaluation_caveat'],'excluded':config['search']['excluded'],'employee_level_rows_persisted':False,'individual_scores_published':False}
    # Atribución adicional con B entrenado y calibrado en idénticos tramos.
    summary['matched_calibration_checks']={
        'ranking':all(p['response']['pr_auc']>p['base_calibrated']['pr_auc'] and p['response']['lift_at_10_percent']>p['base_calibrated']['lift_at_10_percent'] for p in periods),
        **{metric:bool(np.mean([p['response'][metric] for p in periods])<=np.mean([p['base_calibrated'][metric] for p in periods])) for metric in ('brier_score','calibration_error_pp','top_quintile_calibration_error_pp')}}
    write_json(root/'comparison-results.json',summary)
    log('Entrenando el artefacto final al corte disponible con el mismo procedimiento...')
    release=root/'trained-model'
    release.mkdir(exist_ok=True)
    core,selection,calibration,final,_=split_months(monthly,config['knowledge_boundary'],config['search']['selection_intervals'],config['search']['calibration_intervals'])
    winner=(json.loads((release/'selection.json').read_text(encoding='utf-8'))['selected']
            if (release/'selection.json').is_file() else search(core,selection,config,release))
    fitted=fit_final(final,calibration,winner,config)
    artifact=fitted[-1]
    artifact['knowledge_boundary']=config['knowledge_boundary']
    artifact['validation_status']=summary['decision']['status']
    artifact['validation_interpretation']='Los folds evalúan el procedimiento de selección; este artefacto final tiene sus propios coeficientes y selección al corte.'
    write_json(release/'model.json',artifact)
    log(f'Artefacto final creado: {winner["id"]}.')
    manifest={'manifest_version':1,'created_at':utc_now(),'reporting_mode':'presentation','status':'completed','authorization':config['authorization'],'employee_level_rows_persisted':False,'individual_scores_published':False,'model':'trained-model/model.json','decision':summary['decision'],'source_sha256':{w['file']:w['sha256'] for w in metadata['waves']},'config_sha256':sha256_file(root/'experiment-config.yaml'),'code_sha256':{str(Path(__file__).relative_to(ROOT)):sha256_file(Path(__file__))},'artifact_sha256':{str(p.relative_to(root)).replace('\\','/'):sha256_file(p) for p in root.rglob('*.json') if p.name!='manifest.json'}}
    write_json(root/'manifest.json',manifest)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--run-root',type=Path,required=True)
    args=parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    with threadpool_limits(limits=2):
        run(load_config(args.config),args.run_root.resolve())
