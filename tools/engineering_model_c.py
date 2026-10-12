"""C: selección supervisada anidada y grupos interpretables; sólo agregados en disco."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import sys
import time
import warnings

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeRegressor
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.codex/skills/attrition-redshift-db/scripts'))
import run_readonly_query as db
from qvoice_model_validation import weighted_metrics

CONFIG = ROOT/'config/engineering_model_c_20261008.json'


def log(message):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] {message}', flush=True)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=str)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(config, name):
    out = ROOT/config['output']/'input-evidence'
    target = out/(name+'.json')
    if target.exists():
        raise RuntimeError('La evidencia ya existe; revisar antes de ejecutar otra versión.')
    relative = f'queries/audits/engineering_model_c_{name}_20261008.sql'
    query = ROOT/relative
    sql = db.validate_readonly(query.read_text(encoding='utf-8'))
    log(f'Auditoría de entrada: {name}.')
    with db.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [c[0] for c in cursor.description]
            if set(columns) & db.SENSITIVE_OUTPUT_COLUMNS:
                raise RuntimeError('Contrato de salida restringido.')
            rows = [dict(zip(columns, row)) for row in cursor.fetchmany(1001)]
    if len(rows)>1000:
        raise RuntimeError('Evidencia truncada.')
    if name == 'metadata':
        required={('workers_ios_transfers',c) for c in ['employee_id','effective_date','business_process_reason']}
        required|={('post_hire_monthly_worker_dtls',c) for c in ['employee_id','fis_mo_end_dt','region','compa_ratio',
                    'compensation_grade','acquisition','is_transferred','transfer_date','level_grouped','original_hire_date',
                    'service_date','levelentrydate','prior_qc_work_years','worker_supervisory_organization_level_from_top',
                    'work_arrangement','reg_non_intern_dir_reports','is_promo','promotion_date','manager_change',
                    'manager_change_date','manager_employee_id','term_date','term_type','worker_type','employee_type',
                    'active_status','is_rf360_yes_no','eng_or_noneng']}
        okay = required <= {(r['table_name'],r['column_name']) for r in rows}
    else:
        okay = bool(rows) and all(r['employee_count']>=30 and r['contradictory_cells']==0 for r in rows)
    result = {'query': relative, 'sql_sha256': sha(query), 'executed_at': datetime.now(timezone.utc).isoformat(),
              'reporting_mode': 'presentation', 'claim': 'Contrato acotado de entrada; no asigna scores.',
              'outcome': 'pass' if okay else 'fail', 'rows': rows}
    write(target, result)
    text = f'# Entrada {name}\n\nPregunta: ¿la entrada existe y evita contradicciones en persona-snapshot?\n\n'
    text += 'Motivo: evitar que MAX o una unión resuelvan silenciosamente versiones incompatibles.\n\n'
    text += f'Método: SQL `{relative}`. Resultado: **{result["outcome"]}**.\n\n'
    text += 'Impacto en score: ninguno; no es una reevaluación de assessment.\n\n'
    if name!='metadata':
        contract=read(ROOT/'config/engineering_model_c_input_contracts_20261008.json')[name]
        text+=f'Concepto e historia: {contract["meaning"]} Se consulta el valor de cada foto de 2020–2026.\n\n'
        text+=f'Regla previa: {contract["acceptance"]}\n\n'
        text+='Métricas observadas: ver JSON agregado anual adjunto. Acción: '+('habilitar la representación conservadora para el experimento.' if okay else 'resolver la contradicción antes del modelo.')+'\n'
    (out/(name+'.md')).write_text(text,encoding='utf-8')
    log(f'{name}: {result["outcome"]}; {len(rows)} filas agregadas.')
    print(json.dumps(rows,default=str,ensure_ascii=True),flush=True)
    if not okay:
        raise RuntimeError('Entrada no superó la regla previa.')


def raw_features(config):
    return [f for f in config['candidate_features'] if f not in config['interactions'] and f!='calendar_month']


def load_frame(config):
    for name in ['metadata','region','comp_ratio_band','grade_family','acquisition_recorded','transfer_12m','transfer_history']:
        evidence=read(ROOT/config['output']/'input-evidence'/f'{name}.json')
        if evidence['outcome']!='pass' or sha(ROOT/evidence['query'])!=evidence['sql_sha256']:
            raise RuntimeError('Falta evidencia de entrada válida.')
    authorization=read(ROOT/config['authorization'])
    if authorization['status']!='approved' or authorization['non_negotiable_controls']['disk_cache_of_rows']:
        raise RuntimeError('No está vigente la autorización de memoria.')
    template=(ROOT/config['query']).read_text(encoding='utf-8')
    # Lotes de un año para limitar carga de joins en el warehouse y memoria temporal.
    starts=pd.date_range(config['training_start'],config['knowledge_boundary'],freq='YS').tolist()
    starts=[pd.Timestamp(config['training_start'])]+[x for x in starts if x>pd.Timestamp(config['training_start'])]
    ends=[x-pd.Timedelta(days=1) for x in starts[1:]]+[pd.Timestamp(config['knowledge_boundary'])]
    salt=secrets.token_hex(32)
    expected={'snapshot_date','person_key','label_end','y_next','y_6m','company_tenure_band','tenure_julia_band'}|set(raw_features(config))
    parts=[]
    with db.connect() as connection:
        connection.set_session(readonly=True,autocommit=True)
        for start,end in zip(starts,ends):
            begin=time.perf_counter()
            sql=db.validate_readonly(template.replace('__PERIOD_START__',str(start.date())).replace('__PERIOD_END__',str(end.date())).replace('__RUN_SALT__',salt))
            chunk=[]
            with connection.cursor() as cursor:
                cursor.execute(sql)
                columns=[c[0] for c in cursor.description]
                if set(columns)!=expected or set(columns)&db.SENSITIVE_OUTPUT_COLUMNS:
                    raise RuntimeError('Columnas fuera de la lista autorizada.')
                while True:
                    rows=cursor.fetchmany(50000)
                    if not rows:
                        break
                    part=pd.DataFrame(rows,columns=columns)
                    for f in raw_features(config):
                        part[f]=part[f].astype('category')
                    chunk.append(part.drop(columns=['company_tenure_band','tenure_julia_band']))
            local=pd.concat(chunk,ignore_index=True)
            parts.append(local)
            log(f'Carga {start.year}: {len(local):,} persona-mes en memoria; {time.perf_counter()-begin:.1f} s.')
    frame=pd.concat(parts,ignore_index=True)
    del parts,salt,sql
    for c in ['snapshot_date','label_end']:
        frame[c]=pd.to_datetime(frame[c])
    for f in raw_features(config):
        frame[f]=frame[f].astype('category')
    frame['calendar_month']=frame.snapshot_date.dt.month.astype(str).astype('category')
    frame['r6_end']=frame.snapshot_date+pd.DateOffset(months=6)
    if frame.duplicated(['person_key','snapshot_date']).any():
        raise RuntimeError('Duplicado persona-snapshot.')
    if (frame.label_end.notna() & (frame.label_end<=frame.snapshot_date)).any():
        raise RuntimeError('Intervalo mensual inválido.')
    if frame.loc[frame.label_end.isna(),'y_next'].notna().any():
        raise RuntimeError('La última foto tiene etiqueta mensual sin seguimiento.')
    if frame.loc[frame.r6_end>pd.Timestamp(config['knowledge_boundary']),'y_6m'].notna().any():
        raise RuntimeError('R6 etiquetada sin madurar.')
    for label in ['y_next','y_6m']:
        if not frame[label].dropna().isin([0,1]).all():
            raise RuntimeError('Etiqueta no binaria.')
    return frame


def train_before(frame,cutoff):
    return frame.loc[frame.y_next.notna() & (frame.label_end<=pd.Timestamp(cutoff))]


def evaluation(frame,start,n,knowledge):
    dates=sorted(frame.loc[(frame.snapshot_date>=pd.Timestamp(start)) & frame.y_6m.notna() &
                           (frame.r6_end<=pd.Timestamp(knowledge)),'snapshot_date'].unique())[:n]
    if len(dates)!=n:
        raise RuntimeError('Periodo sin seguimiento completo.')
    return frame.loc[frame.snapshot_date.isin(dates)]


@dataclass
class Design:
    features:list
    references:dict
    levels:dict
    columns:list
    interactions:dict

    @classmethod
    def fit(cls,frame,features,interactions):
        references={f:str(frame[f].value_counts().index[0]) for f in features if f not in interactions}
        transformed=cls.prepare(frame,references,interactions)
        levels={f:sorted(transformed[f].astype(str).unique().tolist()) for f in features}
        for f in features:
            if f in interactions:
                references[f]=str(transformed[f].value_counts().index[0])
        columns=['intercept']+[f+'='+v for f in features for v in levels[f] if v!=references[f]]
        return cls(list(features),references,levels,columns,interactions)

    @staticmethod
    def prepare(frame,references,interactions):
        result={f:frame[f].astype(str) for f in references if f in frame}
        for f,(a,b) in interactions.items():
            if a not in references or b not in references:
                continue
            av,bv=frame[a].astype(str),frame[b].astype(str)
            result[f]=pd.Series(np.where((av!=references[a]) & (bv!=references[b]),av+' | '+bv,'ref'),index=frame.index)
        return result

    def matrix(self,frame):
        values=self.prepare(frame,self.references,self.interactions)
        rows=[np.arange(len(frame))];cols=[np.zeros(len(frame),dtype=int)]
        offset=1
        for f in self.features:
            cats=[v for v in self.levels[f] if v!=self.references[f]]
            codes=pd.Categorical(values[f],categories=cats).codes
            valid=codes>=0
            rows.append(np.flatnonzero(valid));cols.append(codes[valid].astype(int)+offset)
            offset+=len(cats)
        rr,cc=np.concatenate(rows),np.concatenate(cols)
        return sparse.csr_matrix((np.ones(len(rr)),(rr,cc)),shape=(len(frame),len(self.columns)))

    def indices(self,features):
        return np.array([i for i,c in enumerate(self.columns) if i==0 or c.split('=',1)[0] in features])


def losses(y,p):
    p=np.clip(np.asarray(p,float),1e-12,1-1e-12)
    y=np.asarray(y,float)
    return {'log_loss':-y*np.log(p)-(1-y)*np.log1p(-p),'brier_score':(y-p)**2}


def hazard(eta):
    return np.clip(-np.expm1(-np.exp(np.clip(eta,-30,5))),1e-8,1-1e-8)


def fit_sparse(x,y,l2,scale=8,max_iter=100):
    """Mismo Fisher scoring de B; matriz dispersa, penalización absoluta l2*8."""
    y=np.asarray(y,float)
    beta=np.zeros(x.shape[1]);beta[0]=np.log(-np.log1p(-np.clip(y.mean(),1e-6,1-1e-6)))
    penalty=np.full(x.shape[1],l2*scale);penalty[0]=0
    for iteration in range(1,max_iter+1):
        eta=x@beta
        exponent=np.exp(np.clip(eta,-30,5));p=hazard(eta)
        derivative=np.maximum(exponent*np.exp(-exponent),1e-10)
        weight=derivative**2/np.maximum(p*(1-p),1e-8)
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


@dataclass
class Model:
    design:Design
    beta:np.ndarray
    features:list
    l2:float
    iterations:int

    def risk_matrix(self,x,months):
        coefficients=np.zeros(len(self.design.columns))
        coefficients[self.design.indices(self.features)]=self.beta
        calendar=np.zeros(13)
        for name,b in zip(self.design.columns,coefficients):
            if name.startswith('calendar_month='):
                calendar[int(name.split('=')[1])]=b
        months=np.asarray(months,int)
        fixed=x@coefficients-calendar[months]
        future=(months[:,None]-1+np.arange(6))%12+1
        # Se recorta cada eta mensual para coincidir exactamente con el predictor B.
        cumulative=np.exp(np.clip(fixed[:,None]+calendar[future],-30,5)).sum(axis=1)
        return np.clip(-np.expm1(-cumulative),1e-8,1-1e-8)

    def risk(self,frame):
        return self.risk_matrix(self.design.matrix(frame),frame.snapshot_date.dt.month.to_numpy())

    def artifact(self):
        indices=self.design.indices(self.features)
        encoder={'features':self.features,'references':{f:self.design.references[f] for f in self.features},
                 'levels':{f:self.design.levels[f] for f in self.features},
                 'columns':[self.design.columns[i] for i in indices],
                 'interactions':{f:v for f,v in self.design.interactions.items() if f in self.features}}
        return {'family':'monthly_cloglog','features':self.features,'l2':self.l2,'penalty_cell_scale':8,
                'iterations':self.iterations,'beta':self.beta.tolist(),'encoder':encoder,
                'formula':'R6 = 1 - product(1 - h_m), calendario avanza; resto congelado',
                'qvoice_included':False,'calibration':'none','status':'experimental'}


def fit_context(design,x,y,features,l2,config):
    beta,iterations=fit_sparse(x[:,design.indices(features)],y,l2,config['penalty_cell_scale'])
    return Model(design,beta,features,l2,iterations)


def metrics(frame,p):
    y=frame.y_6m.to_numpy(float)
    m=weighted_metrics(y,p)
    m['log_loss']=float(losses(y,p)['log_loss'].mean())
    return m


def mean_metrics(rows):
    return {k:float(np.mean([r[k] for r in rows])) for k in rows[0]}


def screen(design,x,y,config):
    sets=[config['base_features'],config['candidate_features']]
    trace=[]
    for c in config['screening_inverse_penalties']:
        estimator=LogisticRegression(penalty='l1',C=c,solver='liblinear',fit_intercept=False,
                                     random_state=config['seed'],tol=1e-5,max_iter=300)
        # El intercepto se penaliza en el filtro solamente; cada candidato se reajusta sin penalizarlo.
        with warnings.catch_warnings(record=True) as notices:
            estimator.fit(x,y)
        if any('converg' in str(w.message).lower() for w in notices):
            trace.append({'C':c,'converged':False});continue
        selected={col.split('=',1)[0] for col,b in zip(design.columns[1:],estimator.coef_[0,1:]) if abs(b)>1e-8}
        for inter,parents in config['interactions'].items():
            if inter in selected:
                selected.update(parents)
        candidate=[f for f in config['candidate_features'] if f in selected]
        trace.append({'C':c,'converged':True,'features':candidate})
        sets.append(candidate)
    unique={tuple(sorted(s)):s for s in sets}
    return list(unique.values()),trace


def select(frame,cutoff,config,out,label):
    trials={};screen_trace=[];candidates=None;dates=[]
    for index,months in enumerate(config['inner_origins_months_before']):
        start=pd.Timestamp(cutoff)-pd.DateOffset(months=months)
        train=train_before(frame,start)
        valid=evaluation(frame,start,config['inner_snapshots'],cutoff)
        if train.empty or train.label_end.max()>start or valid.r6_end.max()>pd.Timestamp(cutoff):
            raise RuntimeError('Partición interna inválida.')
        design=Design.fit(train,config['candidate_features'],config['interactions'])
        x=design.matrix(train);vx=design.matrix(valid);y=train.y_next.to_numpy(float)
        if index==0:
            candidates,screen_trace=screen(design,x,y,config)
        dates.append({'origin':str(start.date()),'train_latest_label':str(train.label_end.max().date()),
                      'validation_first':str(valid.snapshot_date.min().date()),'validation_last':str(valid.snapshot_date.max().date()),
                      'validation_latest_outcome':str(valid.r6_end.max().date())})
        log(f'{label}: validación interna {index+1}/2; {len(candidates)} conjuntos, {len(config["ridge_grid"])} L2.')
        for j,features in enumerate(candidates):
            for l2 in config['ridge_grid']:
                key=(j,l2)
                row=trials.setdefault(key,{'features':features,'l2':l2,'folds':[],'failed':False})
                try:
                    model=fit_context(design,x,y,features,l2,config)
                    p=model.risk_matrix(vx,valid.snapshot_date.dt.month.to_numpy())
                    row['folds'].append(metrics(valid,p))
                except (RuntimeError,np.linalg.LinAlgError) as error:
                    row['failed']=True;row['reason']=str(error)
            if (j+1)%3==0:
                log(f'{label}: {j+1}/{len(candidates)} conjuntos en tramo interno {index+1}.')
        del x,vx,train,valid
    valid_trials=[]
    for row in trials.values():
        if not row['failed'] and len(row['folds'])==2:
            row['mean']=mean_metrics(row['folds']);valid_trials.append(row)
    baseline=[r for r in valid_trials if r['features']==config['base_features']]
    if not baseline:
        raise RuntimeError('No convergió B.')
    b=min(baseline,key=lambda r:(r['mean']['brier_score'],r['l2']))
    gates=config['selection'];bm=b['mean']
    eligible=[r for r in valid_trials if r['mean']['brier_score']<=bm['brier_score']+1e-12 and
              r['mean']['pr_auc']>=bm['pr_auc']*gates['minimum_relative_pr_auc'] and
              r['mean']['lift_at_10_percent']>=bm['lift_at_10_percent']*gates['minimum_relative_lift10']]
    if not eligible:
        raise RuntimeError('B debe ser elegible como respaldo.')
    best=min(r['mean']['log_loss'] for r in eligible)
    near=[r for r in eligible if r['mean']['log_loss']<=best*(1+gates['log_loss_parsimony_tolerance'])]
    chosen=min(near,key=lambda r:(len(r['features']),r['mean']['log_loss'],r['l2']))
    trace={'cutoff':str(pd.Timestamp(cutoff).date()),'dates':dates,'screen':screen_trace,
           'trials':list(trials.values()),'B':b,'C':chosen,'candidates':len(candidates),
           'fits':len(candidates)*len(config['ridge_grid'])*2}
    write(out/'selection'/f'{label}.json',trace)
    log(f'{label}: C selecciona {len(chosen["features"])} términos; L2={chosen["l2"]}.')
    return b,chosen,trace


def group_rules(tree,columns,node=0,path=None):
    path=path or []
    if tree.tree_.children_left[node]==tree.tree_.children_right[node]:
        return {node:path}
    name=columns[tree.tree_.feature[node]]
    return {**group_rules(tree,columns,tree.tree_.children_left[node],path+[{'condition':name,'present':False}]),
            **group_rules(tree,columns,tree.tree_.children_right[node],path+[{'condition':name,'present':True}])}


def make_groups(model,train,config):
    latest=train.loc[train.snapshot_date==train.snapshot_date.max()]
    features=[f for f in model.features if f not in config['interactions'] and f!='calendar_month']
    if not features:
        features=['tenure_playbook_band']  # Sólo describe la población si el modelo es intercepto.
    design=Design.fit(latest,features,{})
    x=design.matrix(latest)[:,1:]
    predictions=model.risk(latest)
    settings=config['groups']
    tree=DecisionTreeRegressor(max_depth=settings['depth'],max_leaf_nodes=settings['maximum_leaves'],
                               min_samples_leaf=settings['minimum_training_people'],random_state=config['seed'])
    tree.fit(x,predictions)
    leaf=tree.apply(x);rules=group_rules(tree,design.columns[1:])
    statistics=[]
    for node,path in rules.items():
        mask=leaf==node
        statistics.append({'node':node,'conditions':path,'training_people':int(mask.sum()),
                           'training_mean_risk':float(predictions[mask].mean())})
    high=[];n=0
    for item in sorted(statistics,key=lambda r:-r['training_mean_risk']):
        high.append(item['node']);n+=item['training_people']
        if n>=len(latest)*settings['target_high_fraction']:
            break
    artifact={'training_snapshot':str(latest.snapshot_date.iloc[0].date()),'rules':statistics,'high_nodes':high,
              'features':features,'encoder':vars(design),'training_r2':float(tree.score(x,predictions)),
              'training_high_fraction':n/len(latest),'maximum_depth':settings['depth']}
    return design,tree,artifact


def group_summary(frame,leaf,artifact,pb,pc,config):
    y=frame.y_6m.to_numpy(float);rows=[]
    for node in np.unique(leaf):
        mask=leaf==node
        people=frame.loc[mask].groupby('snapshot_date').person_key.nunique()
        events=int(y[mask].sum());n=int(mask.sum())
        event_people=int(frame.loc[mask & (y==1),'person_key'].nunique())
        safe=people.min()>=config['groups']['minimum_people_per_snapshot']
        observed=safe and event_people>=config['groups']['minimum_events_for_rates']
        if not safe:
            rows.append({'node':int(node),'suppressed':True});continue
        rows.append({'node':int(node),'exposures':n,'minimum_people_per_snapshot':int(people.min()),
                     'mean_people_per_snapshot':float(people.mean()),'event_exposures':events if observed else None,
                     'distinct_people_with_event':event_people if observed else None,
                     'observed_percent':float(100*y[mask].mean()) if observed else None,
                     'B_predicted_percent':float(100*pb[mask].mean()),'C_predicted_percent':float(100*pc[mask].mean()),
                     'B_error_pp':float(100*abs(pb[mask].mean()-y[mask].mean())) if observed else None,
                     'C_error_pp':float(100*abs(pc[mask].mean()-y[mask].mean())) if observed else None,
                     'high':int(node) in artifact['high_nodes']})
    high=np.isin(leaf,artifact['high_nodes'])
    if frame.loc[high].groupby('snapshot_date').person_key.nunique().min()<30 or frame.loc[high & (y==1),'person_key'].nunique()<30:
        raise RuntimeError('El grupo alto no alcanza el mínimo publicable.')
    overall=y.mean();high_rate=y[high].mean()
    complete=all(r.get('observed_percent') is not None for r in rows)
    summaries={'all_groups_observed_publishable':complete,'high_coverage_percent':float(100*high.mean()),
               'high_capture_percent':float(100*y[high].sum()/y.sum()),'high_lift':float(high_rate/overall),
               'high_observed_percent':float(100*high_rate),
               'high_B_predicted_percent':float(100*pb[high].mean()),'high_C_predicted_percent':float(100*pc[high].mean()),
               'high_B_error_pp':float(100*abs(pb[high].mean()-high_rate)),
               'high_C_error_pp':float(100*abs(pc[high].mean()-high_rate))}
    for name,p in [('B',pb),('C',pc)]:
        summaries[name+'_group_mae_pp']=float(sum((leaf==node).sum()*abs(p[leaf==node].mean()-y[leaf==node].mean()) for node in np.unique(leaf))/len(y)*100)
    return {'summary':summaries,'rows':rows}


def bootstrap(frame,pb,pc,config):
    codes,people=pd.factorize(frame.person_key,sort=False)
    counts=np.bincount(codes);n=len(people)
    lb,lc=losses(frame.y_6m,pb),losses(frame.y_6m,pc)
    sums=np.column_stack([np.bincount(codes,weights=lc[k]-lb[k],minlength=n) for k in lb])
    rng=np.random.default_rng(config['seed']);values=[]
    for _ in range(config['bootstrap_repetitions']):
        weights=np.bincount(rng.integers(n,size=n),minlength=n)
        values.append((weights@sums)/(weights@counts))
    values=np.asarray(values)
    return {k:{'difference_C_minus_B':float(sums[:,j].sum()/counts.sum()),
               'ci95':np.quantile(values[:,j],[.025,.975]).tolist()} for j,k in enumerate(lb)}


def decision(folds,intervals,config):
    b=mean_metrics([f['B'] for f in folds]);c=mean_metrics([f['C'] for f in folds]);d=config['decision']
    gs=[f['groups']['summary'] for f in folds]
    checks={'loss':c['log_loss']<=b['log_loss']*(1-d['minimum_log_loss_improvement']),
            'brier':c['brier_score']<=b['brier_score'],
            'pr_auc':c['pr_auc']>=b['pr_auc']*(1+d['minimum_relative_pr_auc_gain']),
            'lift10':c['lift_at_10_percent']>=b['lift_at_10_percent']*(1+d['minimum_relative_lift10_gain']),
            'temporal_pr':sum(f['C']['pr_auc']>f['B']['pr_auc'] for f in folds)>=d['minimum_winning_folds'],
            'temporal_lift':sum(f['C']['lift_at_10_percent']>f['B']['lift_at_10_percent'] for f in folds)>=d['minimum_winning_folds'],
            'same_groups':np.mean([g['C_group_mae_pp']-g['B_group_mae_pp'] for g in gs])<=d['maximum_group_mae_worsening_pp'],
            'high_group':np.mean([g['high_C_error_pp']-g['high_B_error_pp'] for g in gs])<=d['maximum_high_group_error_worsening_pp'],
            'loss_interval':intervals['log_loss']['ci95'][1]<0}
    checks={k:bool(v) for k,v in checks.items()}
    return {'checks':checks,'passes_all':all(checks.values()),'B_mean':b,'C_mean':c,
            'status':'mejora retrospectiva bajo la regla' if all(checks.values()) else 'C no demuestra mejora suficiente bajo la regla',
            'C_plus_Q_started':False}


def run(config):
    started=time.perf_counter();out=ROOT/config['output']
    if (out/'results.json').exists() or (out/'frozen-config.json').exists():
        raise RuntimeError('El run ya se inició; usar otro output para no sobrescribir evidencia.')
    write(out/'frozen-config.json',config)
    write(out/'frozen-sources.json',{str(p.relative_to(ROOT)):sha(p) for p in [CONFIG,Path(__file__),ROOT/config['query'],ROOT/'config/engineering_model_c_inventory_20261008.json',ROOT/'docs/plans/attrition-model-c-20261008.md']})
    frame=load_frame(config)
    load_seconds=time.perf_counter()-started
    totals=frame.groupby('snapshot_date').agg(exposures=('person_key','size'),people=('person_key','nunique'),
                                                monthly_labeled=('y_next','count'),six_month_labeled=('y_6m','count')).reset_index()
    write(out/'population.json',totals.to_dict('records'))
    folds=[];held=[];bs=[];cs=[];fits=0
    for i,cutoff in enumerate(config['outer_starts'],1):
        fold_start=time.perf_counter();label=f'fold-{i}'
        b,c,trace=select(frame,cutoff,config,out,label);fits+=trace['fits']
        train=train_before(frame,cutoff);test=evaluation(frame,cutoff,config['outer_snapshots'],config['knowledge_boundary'])
        design=Design.fit(train,config['candidate_features'],config['interactions']);x=design.matrix(train)
        models={name:fit_context(design,x,train.y_next.to_numpy(float),spec['features'],spec['l2'],config) for name,spec in [('B',b),('C',c)]}
        fits+=2;tx=design.matrix(test)
        preds={k:m.risk_matrix(tx,test.snapshot_date.dt.month.to_numpy()) for k,m in models.items()}
        gd,tree,ga=make_groups(models['C'],train,config)
        leaf=tree.apply(gd.matrix(test)[:,1:])
        groups=group_summary(test,leaf,ga,preds['B'],preds['C'],config)
        bgd,btree,bga=make_groups(models['B'],train,config)
        bleaf=btree.apply(bgd.matrix(test)[:,1:])
        c_group_score=pd.Series(leaf).map({r['node']:r['training_mean_risk'] for r in ga['rules']}).to_numpy()
        b_group_score=pd.Series(bleaf).map({r['node']:r['training_mean_risk'] for r in bga['rules']}).to_numpy()
        groups['ranking_of_frozen_groups']={'B':metrics(test,b_group_score),'C':metrics(test,c_group_score),
                                            'note':'Comparación de ranking de hojas a igual fracción; empates ponderados. No implica fraccionar grupos en operación.'}
        row={'fold':i,'origin':cutoff,'first_snapshot':str(test.snapshot_date.min().date()),'last_snapshot':str(test.snapshot_date.max().date()),
             'latest_outcome':str(test.r6_end.max().date()),'train_latest_label':str(train.label_end.max().date()),
             'B':metrics(test,preds['B']),'C':metrics(test,preds['C']),'C_features':c['features'],'B_l2':b['l2'],'C_l2':c['l2'],
             'groups':groups,'group_definition':ga,'elapsed_seconds':time.perf_counter()-fold_start}
        folds.append(row);held.append(test[['person_key','y_6m']]);bs.append(preds['B']);cs.append(preds['C'])
        write(out/'folds'/f'{label}.json',row)
        write(out/'folds'/f'{label}-C-model.json',models['C'].artifact())
        log(f'{label} completado en {row["elapsed_seconds"]:.1f} s; log-loss B {row["B"]["log_loss"]:.5f}, C {row["C"]["log_loss"]:.5f}.')
        del x,tx,models,train,test
    combined=pd.concat(held,ignore_index=True);pb=np.concatenate(bs);pc=np.concatenate(cs)
    intervals=bootstrap(combined,pb,pc,config)
    result={'run_id':config['run_id'],'folds':folds,'paired_loss_intervals':intervals,'decision':decision(folds,intervals,config)}
    write(out/'evaluation.json',result)
    # Misma política de selección para el modelo experimental disponible con todos los datos maduros.
    b,c,trace=select(frame,config['knowledge_boundary'],config,out,'final');fits+=trace['fits']
    train=train_before(frame,config['knowledge_boundary']);design=Design.fit(train,config['candidate_features'],config['interactions']);x=design.matrix(train)
    final=fit_context(design,x,train.y_next.to_numpy(float),c['features'],c['l2'],config);fits+=1
    gd,tree,ga=make_groups(final,train,config)
    latest=frame.loc[frame.snapshot_date==frame.snapshot_date.max()];p=final.risk(latest);leaf=tree.apply(gd.matrix(latest)[:,1:])
    forecast=[]
    for node in np.unique(leaf):
        mask=leaf==node
        if mask.sum()>=30:
            forecast.append({'node':int(node),'people':int(mask.sum()),'predicted_risk_6m_percent':float(100*p[mask].mean()),'high':int(node) in ga['high_nodes']})
    final_artifact=final.artifact();final_artifact['knowledge_boundary']=config['knowledge_boundary'];final_artifact['empirical_decision']=result['decision']['status']
    write(out/'trained-model'/'model-c.json',final_artifact)
    write(out/'trained-model'/'groups.json',ga)
    result.update({'final_features':c['features'],'final_l2':c['l2'],'forecast_snapshot':str(latest.snapshot_date.max().date()),
                   'forecast_groups':forecast,'elapsed_seconds':time.perf_counter()-started,'load_seconds':load_seconds,'hazard_fits':fits,
                   'employee_level_rows_persisted':False,'individual_scores_published':False,'qvoice_included':False})
    write(out/'results.json',result)
    write(out/'manifest.json',{'run_id':config['run_id'],'reporting_mode':'presentation','authorization':config['authorization'],
                             'employee_level_rows_persisted':False,'individual_scores_published':False,'salt_persisted':False,
                             'executed_at':datetime.now(timezone.utc).isoformat(),'files':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
                             'elapsed_seconds':result['elapsed_seconds']})
    log(f'Terminado: {result["decision"]["status"]}; {result["elapsed_seconds"]:.1f} s; {fits} ajustes hazard.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--audit');parser.add_argument('--run',action='store_true')
    args=parser.parse_args();config=read(CONFIG)
    with threadpool_limits(limits=1):
        if args.audit:
            audit(config,args.audit)
        elif args.run:
            run(config)
        else:
            parser.error('Elegir --audit o --run')


if __name__=='__main__':
    main()
