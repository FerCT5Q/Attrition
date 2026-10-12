"""Random Survival Forest por foto mensual; datos individuales exclusivamente en RAM."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT/'tools/.deps/rsf'))
import argparse
import gc
import itertools
import secrets
import shutil
import time
from functools import partial
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeRegressor
from threadpoolctl import threadpool_limits
from sksurv.ensemble import RandomSurvivalForest
import sksurv
import sklearn
import rsf_compact_bootstrap as compact_bootstrap
compact_bootstrap.enable()
import engineering_model_c as base
import engineering_c_group_selection as groups
import engineering_c_fourway_groups as four
import compare_engineering_bc_priority as prior
import engineering_model_c_qvoice as cq
import qvoice_horizon_calibration as horizon
import qvoice_model_experiment as qexperiment
from qvoice_model_data import load_config

# Opciones de transporte solo en este proceso; el cliente y sus credenciales
# siguen siendo los del skill Redshift. Detectar conexiones cortadas pronto.
base.db.psycopg2.connect = partial(base.db.psycopg2.connect,keepalives=1,
    keepalives_idle=30,keepalives_interval=10,keepalives_count=3)

write = groups.write
CONFIG = ROOT/'config/engineering_rsf_20261008.json'
BASE_DIMS = ('antiguedad','salidas_equipo','nivel')
B_FEATURES = ['level_grouped','tenure_playbook_band','calendar_month','manager_changes_12m',
              'team_exits_12m','direct_reports_band','time_since_promotion_band','rehire']


def load_frame(config, cconfig, salt, recent_only=False):
    authorization = base.read(ROOT/config['authorization'])
    if authorization['status'] != 'approved' or authorization['non_negotiable_controls']['disk_cache_of_rows']:
        raise RuntimeError('Autorizacion RAM no vigente.')
    for name in ['metadata','region','comp_ratio_band','grade_family','acquisition_recorded','transfer_12m','transfer_history']:
        ev = base.read(ROOT/config['source_c']/'input-evidence'/f'{name}.json')
        if ev['outcome'] != 'pass' or base.sha(ROOT/ev['query']) != ev['sql_sha256']:
            raise RuntimeError('Cambio un contrato de entrada de C.')
    sql_template = (ROOT/config['query']).read_text(encoding='utf-8')
    expected = {'snapshot_date','person_key','label_end','y_next','y_6m','company_tenure_band','tenure_julia_band',
                'same_episode_2024','same_episode_2025','same_episode_2026','voluntary_event_days'} | set(base.raw_features(cconfig))
    parts = []
    first_year = 2025 if recent_only else 2020
    final_date = '2026-02-28' if recent_only else config['knowledge_boundary']
    for year in range(first_year,2027):
        start = max(f'{year}-01-01',cconfig['training_start'])
        end = min(f'{year}-12-31',final_date)
        tick = time.perf_counter()
        sql = base.db.validate_readonly(sql_template.replace('__PERIOD_START__',start).replace('__PERIOD_END__',end).replace('__RUN_SALT__',salt))
        for attempt in range(5):
            year_parts = []
            conn = None
            try:
                conn = base.db.connect()
                conn.set_session(readonly=True,autocommit=True)
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    cols = [c[0] for c in cursor.description]
                    if set(cols) != expected or set(cols) & base.db.SENSITIVE_OUTPUT_COLUMNS:
                        raise RuntimeError('Columnas fuera del contrato.')
                    while True:
                        rows = cursor.fetchmany(50000)
                        if not rows:
                            break
                        part = pd.DataFrame(rows,columns=cols).drop(columns=['company_tenure_band','tenure_julia_band'])
                        for f in base.raw_features(cconfig):
                            part[f] = part[f].astype('category')
                        year_parts.append(part)
                parts.extend(year_parts)
                break
            except (base.db.psycopg2.OperationalError,base.db.psycopg2.InterfaceError) as error:
                failure = {'date':datetime.now(timezone.utc),'year':year,'attempt':attempt+1,
                    'error_type':type(error).__name__,'pgcode':error.pgcode,
                    'categories':[key for key in ['timeout','timed out','ssl','server closed','refused',
                        'translate host','network','authentication','connection reset','eof','canceling statement'] if key in str(error).lower()]}
                failure_path = ROOT/config['output']/'connection-retries.json'
                failures = base.read(failure_path) if failure_path.exists() else []
                write(failure_path,failures+[failure])
                if attempt==4:
                    raise RuntimeError(f'Consulta RAM incompleta en {year}: {type(error).__name__}.') from None
                base.log(f'Reconexion de {year}; se conservan los anos completos en RAM.')
                time.sleep(15)
            finally:
                if conn is not None:
                    conn.close()
        base.log(f'RSF carga {year}: {time.perf_counter()-tick:.1f} s.')
    frame = pd.concat(parts,ignore_index=True)
    del parts,sql
    for f in ['snapshot_date','label_end']:
        frame[f] = pd.to_datetime(frame[f])
    for f in base.raw_features(cconfig):
        frame[f] = frame[f].astype('category')
    frame['calendar_month'] = frame.snapshot_date.dt.month.astype(str).astype('category')
    frame['r6_end'] = frame.snapshot_date+pd.DateOffset(months=6)
    frame['voluntary_event_days'] = pd.to_numeric(frame.voluntary_event_days)
    if frame.duplicated(['person_key','snapshot_date']).any():
        raise RuntimeError('Duplicados persona-foto.')
    # Meses calendario, no seis intervalos de longitud fija.
    dates = frame.snapshot_date
    event_days = frame.voluntary_event_days.to_numpy(float)
    event_bin = np.full(len(frame),7,dtype=np.int8)
    for month in range(6,0,-1):
        limit = ((dates+pd.DateOffset(months=month))-dates).dt.days.to_numpy()
        event_bin[(event_days > 0) & (event_days <= limit)] = month
    frame['event_bin'] = event_bin
    mature = frame.y_6m.notna()
    if not np.array_equal((event_bin[mature] <= 6).astype(int),frame.loc[mature,'y_6m'].to_numpy(int)):
        raise RuntimeError('La etiqueta de supervivencia no reproduce R6.')
    if ((frame.voluntary_event_days.notna()) & (frame.voluntary_event_days <= 0)).any():
        raise RuntimeError('Evento previo o simultaneo al origen.')
    population = frame.groupby('snapshot_date').agg(exposures=('person_key','size'),people=('person_key','nunique'),
        monthly_labeled=('y_next','count'),six_month_labeled=('y_6m','count')).reset_index()
    expected_pop = pd.DataFrame(base.read(ROOT/config['source_c']/'population.json'))
    expected_pop['snapshot_date'] = pd.to_datetime(expected_pop.snapshot_date)
    if recent_only:
        expected_pop = expected_pop.loc[expected_pop.snapshot_date.between('2025-01-01',final_date)].reset_index(drop=True)
    if not population.equals(expected_pop):
        raise RuntimeError('La poblacion difiere de C.')
    return frame,population


def training(frame,cutoff):
    cutoff = pd.Timestamp(cutoff)
    f = frame.loc[frame.snapshot_date < cutoff].copy()
    months = np.zeros(len(f),dtype=np.int8)
    for j in range(1,7):
        months[(f.snapshot_date+pd.DateOffset(months=j)) <= cutoff] = j
    keep = months > 0
    f,months = f.loc[keep],months[keep]
    event = f.event_bin.to_numpy() <= months
    duration = np.where(event,f.event_bin,months).astype(float)
    y = np.empty(len(f),dtype=[('event','?'),('time','<f8')])
    y['event'],y['time'] = event,duration
    if not ((duration >= 1) & (duration <= 6)).all():
        raise RuntimeError('Tiempo fuera de soporte.')
    evidence = {'cutoff':str(cutoff.date()),'first_snapshot':str(f.snapshot_date.min().date()),
        'last_snapshot':str(f.snapshot_date.max().date()),'landmarks':len(f),'people':f.person_key.nunique(),
        'event_landmarks':int(event.sum()),'censored_landmarks':int((~event).sum()),
        'partial_window_landmarks':int((months<6).sum()),'time_bins':list(range(1,7))}
    return f,y,evidence


def encoder_fit(frame,features):
    encoder = OneHotEncoder(handle_unknown='ignore',sparse_output=True,dtype=np.float32)
    x = encoder.fit_transform(frame[features].astype(str)).tocsc()
    return encoder,x


def forest_fit(x,y,spec,config,trees,seed):
    forest = RandomSurvivalForest(n_estimators=trees,max_depth=config['max_depth'],
        min_samples_leaf=spec['min_samples_leaf'],min_samples_split=2*spec['min_samples_leaf'],
        max_features=spec['max_features'],max_samples=min(config['max_samples_per_tree'],len(y)),
        bootstrap=True,n_jobs=config['n_jobs'],random_state=seed,low_memory=False)
    forest.fit(x,y)
    return forest


class ArchivedForest:
    def __init__(self,target):
        self.meta = base.read(target/'model.json')
        self.unique_times_ = np.arange(1,7)
        with np.load(target/self.meta['parameters_file'],allow_pickle=False) as archive:
            self.arrays = {k:archive[k] for k in archive.files}

    def predict_survival_function(self,x,return_array=True):
        x = x.toarray() if sparse.issparse(x) else x
        answer = np.zeros((len(x),6))
        for i in range(self.meta['trees']):
            feature,left,right,threshold,sv = (self.arrays[f'{v}{i}'] for v in ['f','l','r','t','s'])
            nodes = np.zeros(len(x),dtype=np.int32)
            while True:
                active = np.flatnonzero(left[nodes]>=0)
                if not len(active):
                    break
                current = nodes[active]
                nodes[active] = np.where(x[active,feature[current]]<=threshold[current],left[current],right[current])
            answer += sv[nodes]
        return answer/self.meta['trees']


def survival(forest,encoder,features,frame):
    x = encoder.transform(frame[features].astype(str)).tocsr()
    output = []
    indices = np.searchsorted(forest.unique_times_,np.arange(1,7),side='right')-1
    for start in range(0,len(frame),40000):
        values = forest.predict_survival_function(x[start:start+40000],return_array=True)
        output.append(values[:,indices])
    s = np.concatenate(output)
    if not np.isfinite(s).all() or (s < -1e-12).any() or (s > 1+1e-12).any() or (np.diff(s,axis=1)>1e-12).any():
        raise RuntimeError('Curva de supervivencia invalida.')
    return s


def grouped(frame,p,config,dims=BASE_DIMS,artifact=None,details=True):
    if artifact is None:
        raw = [f for f in dims if f not in BASE_DIMS]
        encoded = groups.encode(four.candidate_keys(frame,raw))
        codes,count,names = four.encode_grid(encoded,dims,True)
    else:
        leaf = prior.apply_rules(frame,artifact)
        ids = sorted({int(r['node']) for r in artifact['rules']})
        lookup = {v:i for i,v in enumerate(ids)}
        codes = np.array([lookup[v] for v in leaf])
        count = len(ids)
        names = [next(r['label'] for r in artifact['rules'] if int(r['node'])==v) for v in ids]
    grid = four.FastGrouped(four.context(frame,p),codes,count,config,names)
    if grid.size_metrics()['minimum_eligible_fraction'] < max(config['capacity_fractions']):
        entry,weights = grouped(frame,p,config,BASE_DIMS,None,details)
        entry['fallback_to_common_groups'] = True
        return entry,weights
    entry = {'global':base.metrics(frame,p),'structure':grid.size_metrics(),'scenarios':{},
             'definition':list(dims) if artifact is None else 'surrogate_tree','fallback_to_common_groups':False}
    allocations = {}
    for fraction in config['capacity_fractions']:
        cap = str(round(100*fraction))
        w,low,high = grid.allocation(fraction)
        m,rows = grid.detail(w,with_rows=details)
        if m.get('suppressed'):
            raise RuntimeError('Prioridad no publicable.')
        entry['scenarios'][cap] = {'metrics':m,'selected_groups':rows}
        if details:
            lm,_ = grid.detail(low,False)
            hm,_ = grid.detail(high,False)
            entry['scenarios'][cap].update(whole_groups_excluding_boundary=lm,whole_groups_including_boundary=hm)
        allocations[cap] = w.ravel()[grid.cells]
    return entry,allocations


def select_fit(frame,origin,config,cconfig,target):
    tick = time.perf_counter()
    if (target/'serialization-check.json').exists() and (target/'model.json').exists():
        meta = base.read(target/'model.json')
        encoder = OneHotEncoder(categories=meta['categories'],handle_unknown='ignore',sparse_output=True,dtype=np.float32)
        encoder.fit(pd.DataFrame({f:[c[0]] for f,c in zip(meta['specification']['features'],meta['categories'])}))
        base.log(f'RSF {origin}: se reutiliza el bosque completo archivado.')
        return ArchivedForest(target),encoder,meta['specification'],meta['calibration'],base.read(target/'groups.json')
    dates = sorted(frame.loc[frame.r6_end < pd.Timestamp(origin),'snapshot_date'].unique())[-6:]
    if len(dates)!=6:
        raise RuntimeError('Se requieren seis fotos maduras previas.')
    selection = frame.loc[frame.snapshot_date.isin(dates[:3])]
    calibration = frame.loc[frame.snapshot_date.isin(dates[3:])]
    train,y,info = training(frame,dates[0])
    sets = {'B':B_FEATURES,'all_C_candidates':[f for f in cconfig['candidate_features'] if f not in cconfig['interactions']]}
    candidates,objects = [],{}
    for label,features in sets.items():
        encoder,x = encoder_fit(train,features)
        for leaf,max_features in itertools.product(config['minimum_leaf_grid'],config['max_features_grid']):
            spec = {'id':f'{label}_leaf{leaf}_features{max_features}','feature_set':label,'features':features,
                    'min_samples_leaf':leaf,'max_features':max_features}
            start = time.perf_counter()
            forest = forest_fit(x,y,spec,config,config['selection_trees'],config['seed'])
            p = np.clip(1-survival(forest,encoder,features,selection)[:,-1],1e-8,1-1e-8)
            ev,_ = grouped(selection,p,config,details=False)
            row = {**spec,'global':ev['global'],'priority':ev['scenarios']['30']['metrics'],'seconds':time.perf_counter()-start}
            candidates.append(row)
            write(target/'compact-bootstrap-checks.json',compact_bootstrap.CHECKS)
            objects[spec['id']] = (forest,encoder)
            write(target/'selection-progress.json',{'origin':origin,'candidates':candidates})
            base.log(f'RSF {origin} candidato {len(candidates)}/8: {row["seconds"]:.1f} s; captura {row["priority"]["capture_percent"]:.1f}%.')
        del x
    maximum = max(r['priority']['capture_percent'] for r in candidates)
    near = [r for r in candidates if r['priority']['capture_percent'] >= maximum*(1-config['capture_relative_tolerance'])]
    winner = min(near,key=lambda r:(r['global']['log_loss'],r['priority']['group_snapshot_mae_pp'],-r['min_samples_leaf'],r['id']))
    forest,encoder = objects[winner['id']]
    raw = np.clip(1-survival(forest,encoder,winner['features'],calibration)[:,-1],1e-8,1-1e-8)
    cal = horizon.fit_scalar(calibration.y_6m.to_numpy(float),raw,config['log_multiplier_bounds'])
    cal.update(first_snapshot=str(calibration.snapshot_date.min().date()),last_snapshot=str(calibration.snapshot_date.max().date()),
               latest_outcome=str(calibration.r6_end.max().date()),auxiliary_training_cutoff=str(pd.Timestamp(dates[0]).date()))
    selection_info = {'origin':origin,'auxiliary_training':info,'selection_dates':[str(pd.Timestamp(d).date()) for d in dates[:3]],
                     'calibration_dates':[str(pd.Timestamp(d).date()) for d in dates[3:]],'candidates':candidates,'winner':winner,'calibration':cal}
    write(target/'selection.json',selection_info)
    del objects,forest,encoder,train,y,raw
    gc.collect()
    train,y,info = training(frame,origin)
    encoder,x = encoder_fit(train,winner['features'])
    forest = forest_fit(x,y,winner,config,config['final_trees'],config['seed'])
    last = train.loc[train.snapshot_date==train.snapshot_date.max()]
    p = np.clip(1-survival(forest,encoder,winner['features'],last)[:,-1],1e-8,1-1e-8)
    tree = DecisionTreeRegressor(max_depth=config['surrogate_max_depth'],max_leaf_nodes=config['surrogate_max_leaf_nodes'],
                                min_samples_leaf=config['minimum_group_people_each_snapshot'],random_state=config['seed'])
    xx = encoder.transform(last[winner['features']].astype(str))
    tree.fit(xx,p)
    columns = [f+'='+str(v) for f,values in zip(winner['features'],encoder.categories_) for v in values]
    rules = []
    def walk(node,conditions):
        if tree.tree_.children_left[node] < 0:
            label = ' Y '.join((c['condition'] if c['present'] else 'NO '+c['condition']) for c in conditions) or 'Toda la poblacion'
            rules.append({'node':int(node),'conditions':conditions,'label':label})
            return
        condition = columns[tree.tree_.feature[node]]
        walk(tree.tree_.children_left[node],conditions+[{'condition':condition,'present':False}])
        walk(tree.tree_.children_right[node],conditions+[{'condition':condition,'present':True}])
    walk(0,[])
    artifact = {'rules':rules,'maximum_depth':config['surrogate_max_depth'],'training_r2':tree.score(xx,p),
                'training_snapshot':str(last.snapshot_date.max().date()),'role':'Agrupacion explicativa del bosque; no reemplaza su estimacion.'}
    export_forest(forest,encoder,winner,cal,info,artifact,target,last)
    del train,y,x,xx,tree,last
    gc.collect()
    base.log(f'RSF {origin} seleccionado {winner["id"]}; escalar {cal["multiplier"]:.2f}; total {time.perf_counter()-tick:.1f} s.')
    return forest,encoder,winner,cal,artifact


def export_forest(forest,encoder,spec,cal,training_info,grouping,target,check_frame):
    arrays = {}
    indices = np.searchsorted(forest.unique_times_,np.arange(1,7),side='right')-1
    use_counts = np.zeros(sum(len(c) for c in encoder.categories_),dtype=int)
    for i,est in enumerate(forest.estimators_):
        tree = est.tree_
        arrays[f'f{i}'] = tree.feature.astype(np.int32)
        arrays[f'l{i}'] = tree.children_left.astype(np.int32)
        arrays[f'r{i}'] = tree.children_right.astype(np.int32)
        arrays[f't{i}'] = tree.threshold
        arrays[f's{i}'] = tree.value[:,indices,1]
        use_counts += np.bincount(tree.feature[tree.feature>=0],minlength=len(use_counts))
    target.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(target/'forest-parameters.npz',**arrays)
    metadata = {'family':'RandomSurvivalForest','library':'scikit-survival','library_version':sksurv.__version__,
        'sklearn_version':sklearn.__version__,'origin':training_info['cutoff'],'specification':spec,
        'categories':[c.tolist() for c in encoder.categories_],'trees':len(forest.estimators_),
        'time_months':list(range(1,7)),'calibration':cal,'training':training_info,
        'parameters_file':'forest-parameters.npz','employee_level_rows_persisted':False,'individual_scores_published':False,
        'parameter_contents':'Divisiones y curvas estimadas del modelo; sin muestras, llaves, etiquetas individuales ni conteos por nodo.'}
    write(target/'model.json',metadata)
    write(target/'groups.json',grouping)
    # Reconciliacion de la exportacion de inferencia, con filas efimeras.
    check = check_frame.iloc[:min(1000,len(check_frame))]
    restored = predict_export(target,check)
    original = np.clip(1-survival(forest,encoder,spec['features'],check)[:,-1],1e-8,1-1e-8)
    difference = float(np.max(abs(restored-original)))
    if difference > 1e-10:
        raise RuntimeError('La exportacion del bosque no reproduce el predictor.')
    offset,usage = 0,[]
    for f,cats in zip(spec['features'],encoder.categories_):
        count = int(use_counts[offset:offset+len(cats)].sum())
        usage.append({'feature':f,'split_count':count})
        offset += len(cats)
    write(target/'serialization-check.json',{'outcome':'pass','maximum_absolute_difference':difference,
         'model_split_usage':sorted(usage,key=lambda r:-r['split_count']),
         'interpretation':'Frecuencia de uso; no es importancia causal ni efecto de la variable.'})


def predict_export(target,frame):
    meta = base.read(target/'model.json')
    encoder = OneHotEncoder(categories=meta['categories'],handle_unknown='ignore',sparse_output=False,dtype=np.float32)
    features = meta['specification']['features']
    encoder.fit(pd.DataFrame({f:[c[0]] for f,c in zip(features,meta['categories'])}))
    x = encoder.transform(frame[features].astype(str))
    p = np.zeros(len(frame))
    with np.load(target/meta['parameters_file'],allow_pickle=False) as a:
        for i in range(meta['trees']):
            feature,left,right,threshold,sv = (a[f'{v}{i}'] for v in ['f','l','r','t','s'])
            nodes = np.zeros(len(frame),dtype=np.int32)
            while True:
                active = np.flatnonzero(left[nodes]>=0)
                if not len(active):
                    break
                current = nodes[active]
                go_left = x[active,feature[current]] <= threshold[current]
                nodes[active] = np.where(go_left,left[current],right[current])
            p += 1-sv[nodes,-1]
    return np.clip(p/meta['trees'],1e-8,1-1e-8)


def evaluate(frame,predictions,config,definitions=None):
    entries,allocations = {},{}
    definitions = definitions or {}
    for name,p in predictions.items():
        definition = definitions.get(name,BASE_DIMS)
        entry,weights = grouped(frame,p,config,artifact=definition if isinstance(definition,dict) else None,
                                dims=BASE_DIMS if isinstance(definition,dict) else tuple(definition))
        entries[name],allocations[name] = entry,weights
    ctx = prior.context(frame)
    for name,p in predictions.items():
        if 'C' in allocations:
            encoded = groups.encode(four.candidate_keys(frame,[]))
            codes,_,_ = four.encode_grid(encoded,BASE_DIMS)
            entries[name]['on_C_priority'],_ = prior.describe(ctx,p,allocations['C']['30'],codes)
    return entries,allocations


def summarize_periods(periods):
    names = list(periods[0]['evaluation'])
    summaries = {}
    for name in names:
        summaries[name] = {'global':base.mean_metrics([f['evaluation'][name]['global'] for f in periods]),'scenarios':{}}
        for cap in ['20','30','40']:
            rows = [f['evaluation'][name]['scenarios'][cap]['metrics'] for f in periods]
            summaries[name]['scenarios'][cap] = {k:float(np.mean([row[k] for row in rows])) for k in rows[0]
                if all(isinstance(row.get(k),(int,float)) for row in rows)}
        summaries[name]['groups_mean'] = float(np.mean([f['evaluation'][name]['structure']['mean_eligible_groups'] for f in periods]))
    return summaries


def aggregate(periods,held,config,reference='C'):
    names = list(periods[0]['evaluation'])
    summaries = summarize_periods(periods)
    # Diferencias pareadas, persona como cluster y periodos con igual peso.
    keys,people = pd.factorize(np.concatenate([h['keys'] for h in held]),sort=False)
    variants = [n for n in names if n!=reference]
    specs = [(n,m) for n in variants for m in ['capture20','capture30','capture40','log_loss','brier_score']]
    width = 2+len(specs)
    sums = np.zeros((len(people),len(held),width))
    pos = 0
    for i,h in enumerate(held):
        local = keys[pos:pos+len(h['y'])]; pos += len(h['y'])
        sums[:,i,0] = np.bincount(local,weights=h['y'],minlength=len(people))
        sums[:,i,1] = np.bincount(local,minlength=len(people))
        ref_losses = base.losses(h['y'],h['predictions'][reference])
        for j,(name,metric) in enumerate(specs,2):
            if metric.startswith('capture'):
                cap = metric.removeprefix('capture')
                value = 100*h['y']*(h['allocations'][name][cap]-h['allocations'][reference][cap])
            else:
                value = base.losses(h['y'],h['predictions'][name])[metric]-ref_losses[metric]
            sums[:,i,j] = np.bincount(local,weights=value,minlength=len(people))
    flat = sums.reshape(len(people),-1)
    denominators = np.array([0 if m.startswith('capture') else 1 for _,m in specs])
    def differences(total):
        return (total[:,2:]/total[:,denominators]).mean(axis=0)
    point = differences(sums.sum(axis=0))
    rng = np.random.default_rng(config['seed'])
    draws = []
    for _ in range(config['bootstrap_repetitions']):
        weights = np.bincount(rng.integers(len(people),size=len(people)),minlength=len(people))
        draws.append(differences((weights@flat).reshape(len(held),width)))
    interval = np.quantile(draws,[.025,.975],axis=0)
    comparisons = [{'model':n,'reference':reference,'metric':m,'difference':point[j],'ci95':interval[:,j].tolist()} for j,(n,m) in enumerate(specs)]
    return summaries,comparisons


def restore_bq_inputs(common,qconfig,salt,out):
    """Recrear el contrato historico BQ y alinear en RAM por persona/foto."""
    path = ROOT/'queries/profiles/engineering_qvoice_horizon_calibration_20261008.sql'
    digest = base.sha(path)
    template = path.read_text(encoding='utf-8')
    start,end = str(common.snapshot_date.min().date()),str(common.snapshot_date.max().date())
    sql = base.db.validate_readonly(template.replace('__PERIOD_START__',start).replace('__PERIOD_END__',end).replace('__RUN_SALT__',salt))
    expected = qexperiment.output_columns(qconfig)
    parts = []
    base.log('Restauracion de entradas B + QVoice con su SQL historico.')
    with base.db.connect() as conn:
        conn.set_session(readonly=True,autocommit=True)
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql)
            except base.db.psycopg2.Error as error:
                raise RuntimeError(f'Consulta BQ RAM incompleta: {type(error).__name__}.') from None
            columns = [c[0] for c in cursor.description]
            if columns != expected or set(columns) & base.db.SENSITIVE_OUTPUT_COLUMNS:
                raise RuntimeError('Columnas fuera del contrato historico BQ.')
            while True:
                rows = cursor.fetchmany(50000)
                if not rows:
                    break
                parts.append(pd.DataFrame(rows,columns=columns))
    legacy = pd.concat(parts,ignore_index=True)
    del parts,rows,sql
    for column in ['snapshot_date','label_end']:
        legacy[column] = pd.to_datetime(legacy[column])
    keys = ['person_key','snapshot_date']
    index = pd.MultiIndex.from_frame(legacy[keys])
    target = pd.MultiIndex.from_frame(common[keys])
    duplicate = int(index.duplicated().sum())
    if duplicate or not target.is_unique:
        raise RuntimeError('La alineacion BQ requiere llaves persona-foto unicas.')
    positions = index.get_indexer(target)
    missing = int((positions<0).sum())
    extra = int((~index.isin(target)).sum())
    evidence = {'reporting_mode':'presentation','date':datetime.now(timezone.utc),
        'claim':'Restaurar BQ sobre la misma poblacion; distinguir su etiqueta archivada de la etiqueta comun C/RSF.',
        'semantic_type':'derived_feature','feature':'team_exits_12m',
        'population':'Engineering; Employee; Regular; activo; sin RF360',
        'grain':'persona-foto mensual; solo resultados agregados persistidos',
        'first_snapshot':start,'last_snapshot':end,'knowledge_boundary':qconfig['knowledge_boundary'],
        'query':str(path.relative_to(ROOT)),'sql_sha256':digest,
        'common_query':'queries/profiles/engineering_rsf_person_month_20261008.sql',
        'common_query_sha256':base.sha(ROOT/'queries/profiles/engineering_rsf_person_month_20261008.sql'),
        'method':'Alineacion uno a uno en RAM; igualdad de episodios y etiqueta mensual; reconciliacion auditada de R6; comparacion de bandas.',
        'acceptance_rule':'Cero duplicados/faltantes/adicionales; episodios y y_next iguales; diferencia R6 igual al audit de registro; metricas BQ sobre etiqueta historica dentro de 1e-8.',
        'eligible_rows':len(common),'legacy_rows':len(legacy),'matched_rows':len(common)-missing,
        'unmatched_rows':missing,'extra_rows':extra,'duplicate_rows':duplicate,
        'score_changes':False,'employee_level_rows_persisted':False,'outcome':'pending'}
    if missing or extra:
        write(out/'bq-input-reconciliation.json',evidence)
        raise RuntimeError('Poblacion BQ distinta a la poblacion comun.')
    aligned = legacy.iloc[positions].copy()
    aligned.index = common.index
    invariants = ['label_end','y_next']+[f'same_episode_{w["year"]}' for w in qconfig['sources']['waves']]
    differences = {f:int((~(aligned[f].eq(common[f]) | (aligned[f].isna() & common[f].isna()))).sum()) for f in invariants}
    evidence['invariant_mismatch_counts'] = differences
    if any(differences.values()):
        write(out/'bq-input-reconciliation.json',evidence)
        raise RuntimeError('Etiqueta mensual o episodios BQ distintos a los comunes.')
    audit = base.read(out/'bq-label-contract-audit.json')
    label_counts = {'comparable_rows':len(common),
        'matched_rows':int(aligned.y_6m.eq(common.y_6m).sum()),
        'common_positive_legacy_negative':int((common.y_6m.eq(1)&aligned.y_6m.eq(0)).sum()),
        'common_negative_legacy_positive':int((common.y_6m.eq(0)&aligned.y_6m.eq(1)).sum())}
    evidence['label_contract_counts'] = label_counts
    evidence['label_audit'] = 'bq-label-contract-audit.json'
    if audit['outcome']!='pass' or audit['metrics']!=label_counts or base.sha(ROOT/audit['query'])!=audit['sql_sha256']:
        write(out/'bq-input-reconciliation.json',evidence)
        raise RuntimeError('La discrepancia R6 no coincide con el audit de registro.')
    restored = common.copy()
    restored['y_6m'] = aligned['y_6m']
    changed = {}
    for f in qexperiment.historical.FRAME_FEATURES:
        values = aligned[f].astype(object).fillna('(unknown)').astype(str)
        if f in common:
            changed[f] = int(values.ne(common[f].astype(object).fillna('(unknown)').astype(str)).sum())
        restored[f] = values.astype('category')
    if base.sha(path)!=digest:
        raise RuntimeError('Cambio la consulta BQ archivada.')
    evidence.update(feature_band_mismatch_counts=changed,outcome='pass',
        interpretation='BQ conserva features y etiqueta historicas para reproducir el archivo. Sus predicciones se evaluan con la etiqueta y cortes comunes C; una etiqueta R6 difiere por registro posterior a la frontera global. En team_exits C/RSF exige registro conocido al snapshot.',
        score_impact='No se asignan ni se cambian scores; es una reconciliacion de modelos archivados. Las metricas predictivas se comprueban por periodo por separado.')
    write(out/'bq-input-reconciliation.json',evidence)
    base.log(f'Entradas BQ alineadas: {len(common)} persona-fotos; episodios identicos y diferencia R6 explicada por el audit.')
    return restored


def qvoice_predictions(frame,bq_frame,period,config):
    bqdir = ROOT/'output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1'
    cqdir = ROOT/'output/analysis/engineering/20261008/model-c-plus-qvoice-v1'
    bq = base.read(bqdir/'folds'/period/'model.json')
    ca = base.read(cqdir/'folds'/period/'model.json')
    model = prior.restore_model(ca['base_model'])
    corr = horizon.categorical_eta(ca['correction']['encoder'],ca['correction']['beta'],frame)
    av = horizon.categorical_eta(ca['availability_control']['encoder'],ca['availability_control']['beta'],frame)
    pred = {'C':model.risk(frame),'C_refresh':cq.risk(model,frame,ca['monthly_intercept_control']),
            'C_availability':cq.risk(model,frame,av),'CQ':cq.risk(model,frame,corr)}
    for name in list(pred):
        pred[name+'_scalar'] = horizon.transform_risk(pred[name],ca['calibrators'][name]['log_multiplier'])
    braw = horizon.predict_saved(bq,bq_frame)
    cal = next(r for r in base.read(ROOT/'output/analysis/engineering/20261008/qvoice-horizon-calibration-v1/period-results.json') if r['period']==period)['calibration']
    pred.update(BQ=braw,BQ_monthly_calibrated=horizon.predict_saved(bq,bq_frame,True),BQ_scalar=horizon.transform_risk(braw,cal['log_multiplier']))
    return pred


def complete_run(frame,config,cconfig,out,before,started,load_seconds):
    history,qvoice = base.read(out/'historical-results.json'),base.read(out/'qvoice-results.json')
    forest,encoder,spec,cal,surrogate = select_fit(frame,config['knowledge_boundary'],config,cconfig,out/'trained-model')
    del forest,encoder
    gc.collect()
    if not all(base.sha(ROOT/p)==digest for p,digest in before.items()):
        raise RuntimeError('Cambio un artefacto previo.')
    result = {'run_id':config['run_id'],'reporting_mode':'presentation','created_at':datetime.now(timezone.utc),
        'historical':{k:history[k] for k in ['summary','intervals']},'qvoice':{k:qvoice[k] for k in ['summary','intervals']},
        'final_selected':spec,'final_calibration':cal,'load_seconds':load_seconds,'elapsed_seconds':time.perf_counter()-started,
        'library_version':sksurv.__version__,'base_model_refits':0,'employee_level_rows_persisted':False,'individual_scores_published':False}
    write(out/'results.json',result)
    write(out/'compact-bootstrap-checks.json',compact_bootstrap.CHECKS)
    write(out/'preservation.json',{'unchanged':True,'files':before})
    write(out/'completed.json',{'status':'completed_analysis','seconds':result['elapsed_seconds']})
    write(out/'manifest.json',{'run_id':config['run_id'],'status':'completed_analysis','reporting_mode':'presentation',
        'authorization':config['authorization'],'employee_level_rows_persisted':False,'individual_scores_published':False,
        'files':{str(p.relative_to(out)):base.sha(p) for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'}})
    base.log(f'RSF completo: {result["elapsed_seconds"]:.1f} s; modelos anteriores conservados.')


def run(config_path,resume_setup=False,resume=False,phase='all'):
    started = time.perf_counter()
    config = base.read(config_path)
    out = ROOT/config['output']
    if phase!='all':
        if not resume or not (out/'historical-results.json').exists():
            raise RuntimeError('Las fases parciales requieren reanudar la historia ya completa.')
        if phase=='comparison' and not all((out/'folds'/origin/'serialization-check.json').exists() for origin in config['origins']):
            raise RuntimeError('Faltan bosques historicos completos.')
        if phase=='final' and not (out/'qvoice-results.json').exists():
            raise RuntimeError('Completar la comparacion QVoice antes del modelo final.')
    if (out/'started.json').exists():
        if (not resume and (not resume_setup or list((out/'folds').glob('*/selection-progress.json')))) or (out/'results.json').exists():
            raise RuntimeError('Ejecucion existente: usar carpeta nueva o revisar interrupcion.')
        if resume and base.read(out/'frozen-config.json') != config:
            raise RuntimeError('Configuracion diferente a la ejecucion interrumpida.')
        interruption = 'evaluation-interruption.json' if resume else 'setup-interruption.json'
        if not (out/interruption).exists():
            write(out/interruption,{'previous_start':base.read(out/'started.json'),
            'reason':'Normalizacion de IDs numericos de hojas archivadas.' if resume else 'Windows sandbox denied the ThreadPool internal pipe before the first candidate completed.',
            'action':'Reanudar con los bosques completos guardados; mismos datos, configuracion y criterios.',
            'previous_source_hashes':base.read(out/'frozen-sources.json')})
    cconfig = base.read(ROOT/config['source_c']/'frozen-config.json')
    original = base.read(ROOT/config['source_c']/'results.json')
    four_results = base.read(ROOT/'output/analysis/engineering/20261008/c-fourway-groups-v1/results.json')
    old_dirs = ['model-c-v2','c-group-selection-v1','c-fourway-groups-v1','model-c-plus-qvoice-v1',
                'qvoice-model-b-calibrated-v1','qvoice-horizon-calibration-v1','bc-priority-comparison-v1']
    before = {str(p.relative_to(ROOT)):base.sha(p) for d in old_dirs
              for p in (ROOT/'output/analysis/engineering/20261008'/d).rglob('*') if p.is_file()}
    with base.db.connect() as conn:
        conn.set_session(readonly=True,autocommit=True)
    write(out/'started.json',{'date':datetime.now(timezone.utc),'status':'running','phase':phase})
    write(out/'frozen-config.json',config)
    files = [config_path,Path(__file__),ROOT/config['query'],ROOT/config['authorization'],
             ROOT/'docs/plans/engineering-random-survival-forest-20261008.md',
             ROOT/'docs/plans/engineering-rsf-bq-input-reconciliation-20261008.md',
             ROOT/'docs/plans/engineering-rsf-bq-input-reconciliation-20261009-v2.md',
             ROOT/'queries/audits/engineering_rsf_bq_label_contract_20261009.sql',
             ROOT/'tools/rsf_bq_label_audit.py',
             ROOT/'queries/profiles/engineering_qvoice_horizon_calibration_20261008.sql']
    files += [ROOT/'tools'/name for name in ['engineering_model_c.py','engineering_c_group_selection.py','engineering_c_fourway_groups.py',
        'compare_engineering_bc_priority.py','engineering_model_c_qvoice.py','qvoice_horizon_calibration.py','qvoice_model_validation.py',
        'qvoice_model_experiment.py','qvoice_model_data.py','rsf_compact_bootstrap.py']]
    for file in files:
        dest = out/'source'/file.relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(file,dest)
    write(out/'frozen-sources.json',{str(p.relative_to(ROOT)):base.sha(p) for p in files})
    salt = secrets.token_hex(32)
    frame,population = load_frame(config,cconfig,salt,recent_only=phase=='comparison')
    suffix = '-recent' if phase=='comparison' else ''
    write(out/f'population{suffix}.json',population.to_dict('records'))
    write(out/f'input-checks{suffix}.json',{'population_reproduced':True,'survival_event_reproduces_y6':True,
        'duplicate_person_snapshots':0,'event_dates_after_snapshot':True,'rows_persisted':False,
        'query':config['query'],'date':datetime.now(timezone.utc),'score_changes':False})
    load_seconds = time.perf_counter()-started
    if phase=='final':
        del salt
        complete_run(frame,config,cconfig,out,before,started,load_seconds)
        return
    periods,held,recent_memory = [],[],{}
    for index,origin in enumerate(config['origins']):
        target = out/'folds'/origin
        if resume and index < 3 and (out/'historical-results.json').exists() and (target/'evaluation.json').exists():
            periods.append(base.read(target/'evaluation.json'))
            base.log(f'RSF {origin}: se conserva la evaluacion agregada completa.')
            continue
        forest,encoder,spec,cal,surrogate = select_fit(frame,origin,config,cconfig,target)
        test = base.evaluation(frame,origin,6 if index<4 else 2,config['knowledge_boundary'])
        s = survival(forest,encoder,spec['features'],test)
        raw = np.clip(1-s[:,-1],1e-8,1-1e-8)
        calibrated = horizon.transform_risk(raw,cal['log_multiplier'])
        historic = original['folds'][min(index,3)]
        b = prior.restore_model(base.read(ROOT/'output/analysis/engineering/20261008/bc-priority-comparison-v1/reconstructed-models'/f'fold-{min(index,3)+1}-B.json'))
        c = prior.restore_model(base.read(ROOT/config['source_c']/'folds'/f'fold-{min(index,3)+1}-C-model.json'))
        pred = {'B':b.risk(test),'C':c.risk(test),'RSF_raw':raw,'RSF':calibrated,'RSF_tree':calibrated}
        definitions = {'RSF_tree':surrogate}
        f4 = four_results['folds'][min(index,3)]
        for name in ['C_plus1','C_four','C_near40']:
            pred[name] = pred['C']
            definitions[name] = f4['selections'][name]['definition']['dimensions']
        pred['C_tree'] = pred['C']
        definitions['C_tree'] = historic['group_definition']
        # Etiquetas legibles de las reglas archivadas, sin alterar sus cortes.
        definitions['C_tree'] = {**definitions['C_tree'],'rules':[{**r,'label':r.get('label',' Y '.join(c['condition'] if c['present'] else 'NO '+c['condition'] for c in r['conditions']))} for r in definitions['C_tree']['rules']]}
        if index<4:
            prior.compare_metrics(base.metrics(test,pred['B']),historic['B'],1e-8,'B archivado')
            prior.compare_metrics(base.metrics(test,pred['C']),historic['C'],1e-8,'C archivado')
        ev,allocation = evaluate(test,pred,config,definitions)
        record = {'origin':origin,'first_snapshot':str(test.snapshot_date.min().date()),'last_snapshot':str(test.snapshot_date.max().date()),
            'latest_outcome':str(test.r6_end.max().date()),'people':test.person_key.nunique(),'exposures':len(test),
            'selection':spec['id'],'calibration':cal,'evaluation':ev}
        write(target/'evaluation.json',record)
        if index<4:
            periods.append(record)
            held.append({'keys':test.person_key.to_numpy(),'y':test.y_6m.to_numpy(float),'predictions':pred,'allocations':allocation})
        if index==3:
            mask = test.snapshot_date.dt.year.eq(2025).to_numpy()
            recent_memory['aug_dec_2025'] = {'index':test.index[mask].to_numpy(),'predictions':{k:v[mask] for k,v in pred.items()},'definitions':definitions}
            ext = frame.loc[frame.snapshot_date==pd.Timestamp('2026-02-22')]
            eraw = np.clip(1-survival(forest,encoder,spec['features'],ext)[:,-1],1e-8,1-1e-8)
            ep = {'B':b.risk(ext),'C':c.risk(ext),'RSF_raw':eraw,'RSF':horizon.transform_risk(eraw,cal['log_multiplier'])}
            extension,_ = evaluate(ext,ep,config)
            write(out/'extension.json',{'snapshot':'2026-02-22','model_origin':origin,'people':len(ext),'evaluation':extension})
        elif index==4:
            recent_memory['jan_feb_2026'] = {'index':test.index.to_numpy(),'predictions':pred,'definitions':definitions}
        del forest,encoder,test,s,raw,calibrated
        gc.collect()
    if resume and (out/'historical-results.json').exists():
        saved = base.read(out/'historical-results.json')
        summary,intervals = summarize_periods(periods),saved['intervals']
    else:
        summary,intervals = aggregate(periods,held,config)
    write(out/'historical-results.json',{'periods':periods,'summary':summary,'intervals':intervals})
    del held
    gc.collect()
    # QVoice se enlaza una sola vez, con la misma llave efimera de la carga.
    qconfig = load_config(ROOT/'config/qvoice_model_calibrated_20261008.yaml')
    metadata = base.read(ROOT/'output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/preflight/source-metadata.json')
    needed = set()
    for period in recent_memory:
        for folder in ['qvoice-model-b-calibrated-v1','model-c-plus-qvoice-v1']:
            artifact = base.read(ROOT/'output/analysis/engineering/20261008'/folder/'folds'/period/'model.json')
            needed.update(artifact['correction']['encoder']['features'])
    qframe = horizon.attach_selected(frame.loc[frame.snapshot_date>='2025-01-01'],qconfig,metadata,salt,sorted(needed),{})
    qindices = np.unique(np.concatenate([r['index'] for r in recent_memory.values()]))
    bq_frame = restore_bq_inputs(qframe.loc[qindices],qconfig,salt,out)
    del salt
    for f in needed:
        qframe['av_'+f] = pd.Series(np.where(qframe[f].astype(str).isin(cq.VALID),'available',qframe[f].astype(str)),index=qframe.index).astype('category')
    qperiods,qheld = [],[]
    for period,remembered in recent_memory.items():
        test = qframe.loc[remembered['index']]
        pred = {**remembered['predictions'],**qvoice_predictions(test,bq_frame.loc[test.index],period,config)}
        ev,allocation = evaluate(test,pred,config,remembered['definitions'])
        old_cq = base.read(ROOT/'output/analysis/engineering/20261008/model-c-plus-qvoice-v1/folds'/period/'evaluation.json')
        for name in cq.NAMES:
            prior.compare_metrics(ev[name]['global'],old_cq['evaluation'][name]['global'],1e-8,'C QVoice archivado')
        old_bq = next(r for r in base.read(ROOT/'output/analysis/engineering/20261008/qvoice-horizon-calibration-v1/period-results.json') if r['period']==period)
        reconciliation = {}
        for name,previous in [('BQ','uncalibrated'),('BQ_scalar','scalar'),('BQ_monthly_calibrated','previous')]:
            actual,expected = base.metrics(bq_frame.loc[test.index],pred[name]),old_bq['metrics'][previous]
            differences = {key:actual[key]-expected[key] for key in ['exposures','event_exposures','pr_auc','lift_at_10_percent',
                'log_loss','brier_score','predicted_percent','observed_percent']}
            if any(abs(value)>1e-8 for value in differences.values()):
                write(out/'qvoice-reconciliation-failure.json',{'period':period,'variant':name,'differences':differences})
                raise RuntimeError('Metricas B QVoice no reconciliadas con sus entradas historicas.')
            reconciliation[name] = {'outcome':'pass','all_metrics_reproduced':True,'differences':differences,
                'common_label_evaluation_difference':{key:ev[name]['global'][key]-expected[key] for key in differences},
                'input_contract':'Reproduccion del archivo con etiqueta BQ historica; comparacion final con etiqueta y grupos comunes C.'}
        write(out/'qvoice-comparison'/f'{period}-reconciliation.json',reconciliation)
        record = {'period':period,'first_snapshot':str(test.snapshot_date.min().date()),'last_snapshot':str(test.snapshot_date.max().date()),
                  'latest_outcome':str(test.r6_end.max().date()),'people':test.person_key.nunique(),'exposures':len(test),'evaluation':ev}
        qperiods.append(record)
        qheld.append({'keys':test.person_key.to_numpy(),'y':test.y_6m.to_numpy(float),'predictions':pred,'allocations':allocation})
        write(out/'qvoice-comparison'/f'{period}.json',record)
    qsummary,qintervals = aggregate(qperiods,qheld,config)
    write(out/'qvoice-results.json',{'periods':qperiods,'summary':qsummary,'intervals':qintervals})
    del qheld,qframe,bq_frame,recent_memory
    gc.collect()
    if phase=='comparison':
        if not all(base.sha(ROOT/p)==digest for p,digest in before.items()):
            raise RuntimeError('Cambio un artefacto previo.')
        write(out/'comparison-completed.json',{'date':datetime.now(timezone.utc),'status':'completed_comparison',
            'seconds':time.perf_counter()-started,'load_seconds':load_seconds,'previous_models_preserved':True})
        base.log('Comparacion QVoice completa y guardada; resta el bosque final.')
        return
    complete_run(frame,config,cconfig,out,before,started,load_seconds)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=CONFIG)
    parser.add_argument('--resume-setup',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--phase',choices=['all','comparison','final'],default='all')
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(args.config,args.resume_setup,args.resume,args.phase)
