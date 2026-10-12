"""Cruces interpretables de cuatro variables; C congelado y filas sólo en RAM."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import itertools
import math
import shutil
import time

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import engineering_model_c as base
import engineering_c_group_selection as old
import compare_engineering_bc_priority as prior

ROOT = base.ROOT
DEFAULT = ROOT/'config/engineering_c_fourway_groups_20261008.json'
BASE = ('antiguedad', 'salidas_equipo', 'nivel')
NAMES = {'C_current':'C · cortes actuales', 'C_plus1':'C · cortes actuales + una variable',
         'C_four':'C · cuatro variables seleccionadas', 'C_near40':'C · búsqueda de 30–50 grupos'}
DISPLAY = {**old.historical.DISPLAY, 'manager_changes_12m':'Cambios de manager en 12 meses',
 'direct_reports_band':'Reportes directos', 'time_since_promotion_band':'Última promoción',
 'rehire':'Recontratación', 'prior_experience_band':'Experiencia previa', 'time_at_level_band':'Tiempo en el nivel',
 'manager_left_6m':'Salida previa del manager', 'ios_12m':'Movimientos IOS en 12 meses',
 'layers_band':'Capa organizativa almacenada', 'work_arrangement_group':'Modalidad de trabajo',
 'region':'Región', 'comp_ratio_band':'Banda de comp ratio', 'grade_family':'Familia de grado',
 'acquisition_recorded':'Adquisición registrada', 'transfer_12m':'Transferencia en 12 meses'}
write = old.write


def candidate_keys(frame, features):
    keys = old.historical.coarse_keys(frame)[list(BASE)].copy()
    excluded = {'tenure_playbook_band', 'team_exits_12m', 'level_grouped', 'calendar_month'}
    for f in features:
        if f not in excluded and '_x_' not in f:
            keys[f] = frame[f].astype(str)
    return keys


def category_es(value):
    return (value.replace('years','años').replace('year','año').replace('months','meses')
            .replace('(unknown)','sin dato').replace('no recorded','sin registro')
            .replace('yes','sí').replace('promo ','promoción '))


def encode_grid(encoded, dims, labels=False):
    codes = np.zeros(len(encoded[dims[0]][0]), dtype=np.int64)
    count = 1
    for dim in dims:
        size = len(encoded[dim][1])
        codes = codes*size+encoded[dim][0]
        count *= size
    names = None
    if labels:
        names = []
        for index in range(count):
            bits = []
            for dim in reversed(dims):
                index, remainder = divmod(index, len(encoded[dim][1]))
                bits.append(DISPLAY.get(dim,dim)+': '+category_es(encoded[dim][1][remainder]))
            names.append(' · '.join(reversed(bits)))
    return codes, count, names


def context(frame, pred):
    ctx = prior.context(frame)
    ctx.update(pred=pred, dates=sorted(frame.snapshot_date.unique()))
    return ctx


class FastGrouped(old.Grouped):
    def __init__(self, ctx, codes, count, config, names=None):
        self.frame, self.pred, self.codes = ctx['frame'], ctx['pred'], codes
        self.names = names or []
        self.config, self.dates, self.date_values = config, ctx['date_codes'], ctx['dates']
        self.y, self.keys = ctx['y'], ctx['keys']
        self.cells = self.dates*count+codes
        shape = (ctx['date_count'], count)
        self.n = np.bincount(self.cells, minlength=np.prod(shape)).reshape(shape)
        self.e = np.bincount(self.cells, weights=self.y, minlength=np.prod(shape)).reshape(shape)
        self.p = np.bincount(self.cells, weights=self.pred, minlength=np.prod(shape)).reshape(shape)
        self.score = np.divide(self.p,self.n,out=np.zeros(shape),where=self.n>0)
        self.eligible = self.n >= config['minimum_group_people_each_snapshot']

    def size_metrics(self):
        size = self.eligible.sum(axis=1)
        mass = (self.n*self.eligible).sum(axis=1)/self.n.sum(axis=1)
        return {'mean_eligible_groups':float(size.mean()), 'minimum_eligible_groups':int(size.min()),
                'maximum_eligible_groups':int(size.max()), 'minimum_eligible_fraction':float(mass.min()),
                'rest_percent':float(100*self.n[~self.eligible].sum()/self.n.sum())}


def search(frame, pred, features, config):
    ctx = context(frame,pred)
    encoded = old.encode(candidate_keys(frame,features))
    varying = [k for k,(_,v) in encoded.items() if len(v)>1]
    codes,count,names = encode_grid(encoded,BASE,True)
    control = FastGrouped(ctx,codes,count,config,names)
    cw,_,_ = control.allocation(config['primary_capacity_fraction'])
    rw = cw.ravel()[control.cells]
    control_residual = rw*(pred-ctx['y'])
    denominator = rw.sum()
    candidates = []
    for index,dims in enumerate(itertools.combinations(varying,config['combination_size']),1):
        codes,count,_ = encode_grid(encoded,dims)
        grid = FastGrouped(ctx,codes,count,config)
        structure = grid.size_metrics()
        admissible = (structure['maximum_eligible_groups'] <= config['maximum_development_groups_each_snapshot'] and
                      structure['minimum_eligible_fraction'] >= config['minimum_development_eligible_fraction_each_snapshot'])
        record = {'dimensions':list(dims),'name':' × '.join(dims),'kind':'cut', **structure, 'admissible':bool(admissible)}
        if admissible:
            w,_,_ = grid.allocation(config['primary_capacity_fraction'])
            metric = grid.quick(w)
            # Cada persona aparece como máximo una vez por fecha. Esta cota
            # conservadora garantiza 30 personas distintas con evento sin publicar grupos pequeños.
            publication_ok = float((w*grid.e).sum())/ctx['date_count'] >= config['minimum_distinct_events']
            record['admissible'] = publication_ok
            if publication_ok:
                residual = np.bincount(grid.cells,weights=control_residual,minlength=grid.n.size).reshape(grid.n.shape)
                fine_error = 100*abs(residual).sum()/denominator
                record.update(metric, control_same_partition_group_snapshot_mae_pp=fine_error,
                              excess_group_snapshot_mae_pp=metric['group_snapshot_mae_pp']-fine_error)
        candidates.append(record)
        if index % 500 == 0:
            base.log(f'Búsqueda: {index} cruces de cuatro variables procesados.')
    selected = {}
    baseline = {'kind':'cut','dimensions':list(BASE),'name':' × '.join(BASE)}
    for name in NAMES:
        if name == 'C_current':
            selected[name] = {'definition':baseline,'fallback':False,'admissible_candidates':1}
            continue
        pool = [x for x in candidates if x['admissible']]
        if name == 'C_plus1':
            pool = [x for x in pool if set(BASE).issubset(x['dimensions'])]
        elif name == 'C_near40':
            lower,upper = config['target_group_range']
            pool = [x for x in pool if lower <= x['mean_eligible_groups'] <= upper]
        if not pool:
            selected[name] = {'definition':baseline,'fallback':True,'reason':'Sin candidatos admisibles en desarrollo','admissible_candidates':0}
            continue
        highest = max(x['capture_percent'] for x in pool)
        close = [x for x in pool if x['capture_percent'] >= highest*(1-config['capture_relative_tolerance'])]
        error = min(x['excess_group_snapshot_mae_pp'] for x in close)
        close = [x for x in close if x['excess_group_snapshot_mae_pp'] <= error+config['error_tolerance_pp']]
        win = min(close,key=lambda x:(x['mean_eligible_groups'],-x['capture_percent'],x['name']))
        selected[name] = {'definition':{k:win[k] for k in ['kind','dimensions','name']},'winner_metrics':win,
                          'fallback':False,'admissible_candidates':len(pool),'candidates_after_tolerance':len(close)}
    return candidates,selected


def evaluate(frame,pred,features,selections,config):
    ctx = context(frame,pred)
    encoded = old.encode(candidate_keys(frame,features))
    outputs, allocations = {}, {str(round(f*100)):{} for f in config['capacity_fractions']}
    control_weights = {}
    for name,choice in selections.items():
        spec = choice['definition']
        codes,count,names = encode_grid(encoded,spec['dimensions'],True)
        grid = FastGrouped(ctx,codes,count,config,names)
        fallback = grid.size_metrics()['minimum_eligible_fraction'] < max(config['capacity_fractions'])
        if fallback:
            spec = selections['C_current']['definition']
            codes,count,names = encode_grid(encoded,spec['dimensions'],True)
            grid = FastGrouped(ctx,codes,count,config,names)
        entry = {'definition':spec,'requested_definition':choice['definition'], 'development_fallback':choice['fallback'],
                 'external_fallback':fallback,'structure':grid.size_metrics(),'scenarios':{}}
        for fraction in config['capacity_fractions']:
            cap = str(round(fraction*100))
            w,low,high = grid.allocation(fraction)
            metric,rows = grid.detail(w)
            if metric.get('suppressed'):
                raise RuntimeError('Prioridad agregada sin mínimos de publicación.')
            lw,_ = grid.detail(low,False)
            hw,_ = grid.detail(high,False)
            rw = w.ravel()[grid.cells]
            allocations[cap][name] = rw
            if name == 'C_current':
                control_weights[cap] = rw
            comparable,_ = prior.describe(ctx,pred,control_weights[cap],codes)
            if comparable.get('suppressed'):
                raise RuntimeError('Control comparable no publicable.')
            entry['scenarios'][cap] = {'metrics':metric,'selected_groups':rows,
                'control_on_same_partition':comparable,'whole_groups_excluding_boundary':lw,'whole_groups_including_boundary':hw}
        outputs[name] = entry
    return outputs,allocations


def uncertainty(held,config):
    variants = [x for x in NAMES if x!='C_current']
    capacities = list(held[0]['allocations'])
    codes,people = pd.factorize(np.concatenate([h['keys'] for h in held]),sort=False)
    width = 1+len(variants)*len(capacities)
    sums = np.zeros((len(people),len(held),width))
    offset=0
    combinations=list(itertools.product(capacities,variants))
    for i,h in enumerate(held):
        local=codes[offset:offset+len(h['y'])]
        offset+=len(local)
        sums[:,i,0]=np.bincount(local,weights=h['y'],minlength=len(people))
        for j,(cap,name) in enumerate(combinations,1):
            delta=h['allocations'][cap][name]-h['allocations'][cap]['C_current']
            sums[:,i,j]=np.bincount(local,weights=h['y']*delta,minlength=len(people))
    flat=sums.reshape(len(people),-1)
    rng=np.random.default_rng(config['seed'])
    draws=[]
    for _ in range(config['bootstrap_repetitions']):
        w=np.bincount(rng.integers(len(people),size=len(people)),minlength=len(people))
        total=(w@flat).reshape(len(held),width)
        draws.append(np.mean(100*total[:,1:]/total[:,:1],axis=0))
    total=sums.sum(axis=0)
    point=np.mean(100*total[:,1:]/total[:,:1],axis=0)
    ci=np.quantile(draws,[.025,.975],axis=0)
    return [{'capacity':cap,'variant':name,'difference_pp':point[j],'ci95_pp':ci[:,j]} for j,(cap,name) in enumerate(combinations)]


def summarize(folds,intervals,config):
    result={}
    for cap in ['20','30','40']:
        result[cap]={}
        for name in NAMES:
            rows=[f['evaluation'][name]['scenarios'][cap]['metrics'] for f in folds]
            metrics={k:float(np.mean([r[k] for r in rows])) for k in rows[0]
                     if all(isinstance(r.get(k),(int,float,np.number)) for r in rows)}
            control=[f['evaluation'][name]['scenarios'][cap]['control_on_same_partition'] for f in folds]
            comparable={k:float(np.mean([r[k] for r in control])) for k in ['group_mae_pp','group_snapshot_mae_pp']}
            structure={k:float(np.mean([f['evaluation'][name]['structure'][k] for f in folds])) for k in folds[0]['evaluation'][name]['structure']}
            entry={'metrics':metrics,'control_on_same_partition':comparable,'structure':structure,
                   'distinct_definitions':len({tuple(f['selections'][name]['definition']['dimensions']) for f in folds}),
                   'development_fallbacks':sum(f['selections'][name]['fallback'] for f in folds),
                   'external_fallbacks':sum(f['evaluation'][name]['external_fallback'] for f in folds)}
            if name!='C_current':
                ci=next(v for v in intervals if v['capacity']==cap and v['variant']==name)
                changes=[f['evaluation'][name]['scenarios'][cap]['metrics']['capture_percent']-
                         f['evaluation']['C_current']['scenarios'][cap]['metrics']['capture_percent'] for f in folds]
                wins=sum(x>1e-9 for x in changes)
                guard={k:metrics[k]<=comparable[k]+config['error_tolerance_pp'] for k in comparable}
                entry.update(comparison=ci,winning_periods=wins,losing_periods=sum(x < -1e-9 for x in changes),
                             error_checks=guard,meets_rule=bool(ci['ci95_pp'][0]>0 and wins>=3 and all(guard.values())))
            result[cap][name]=entry
    return result


def run(path):
    start=time.perf_counter()
    config=base.read(path)
    out=ROOT/config['output']
    if (out/'started.json').exists():
        raise RuntimeError('Run existente: usar una carpeta nueva.')
    source=ROOT/config['source_c']
    ref=ROOT/config['source_groups']
    original=base.read(source/'results.json')
    previous=base.read(ref/'results.json')
    bc=base.read(source/'frozen-config.json')
    protected=[source,ref,ROOT/'output/analysis/engineering/20261008/model-c-plus-qvoice-v1',
               ROOT/'output/analysis/engineering/20261008/model-c-priority-groups-v1',
               ROOT/'output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1',
               ROOT/'output/analysis/engineering/20261008/qvoice-horizon-calibration-v1']
    before={str(p.relative_to(ROOT)):base.sha(p) for d in protected for p in d.rglob('*') if p.is_file()}
    frozen=base.read(source/'frozen-sources.json')
    if base.sha(ROOT/bc['query'])!=frozen[bc['query'].replace('/','\\')]:
        raise RuntimeError('Cambió la consulta de C.')
    for module in ['tools/engineering_model_c.py','tools/engineering_model_c_fast.py']:
        if base.sha(ROOT/module)!=base.sha(source/'source'/module):
            raise RuntimeError('Motor distinto al archivado.')
    with base.db.connect() as conn:
        conn.set_session(readonly=True,autocommit=True)
    write(out/'started.json',{'started_at':datetime.now(timezone.utc),'status':'running'})
    files=[path,Path(__file__),ROOT/bc['query'],ROOT/config['authorization'],ROOT/'docs/plans/engineering-c-fourway-groups-20261008.md',
           ROOT/'tools/engineering_model_c.py',ROOT/'tools/engineering_c_group_selection.py',ROOT/'tools/engineering_playbook_group_selection.py',
           ROOT/'tools/compare_engineering_bc_priority.py']
    for file in files:
        dest=out/'source'/file.relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(file,dest)
    write(out/'frozen-sources.json',{str(p.relative_to(ROOT)):base.sha(p) for p in files})
    write(out/'frozen-config.json',config)
    base.log('Carga única en RAM; se restauran cuatro C, cero reajustes hazard.')
    frame=base.load_frame(bc)
    load_seconds=time.perf_counter()-start
    population=frame.groupby('snapshot_date').agg(exposures=('person_key','size'),people=('person_key','nunique'),
                  monthly_labeled=('y_next','count'),six_month_labeled=('y_6m','count')).reset_index()
    expected=pd.DataFrame(base.read(source/'population.json'))
    expected['snapshot_date']=pd.to_datetime(expected.snapshot_date)
    if not population.equals(expected):
        raise RuntimeError('Población o madurez diferente a C.')
    write(out/'population.json',population.to_dict('records'))
    folds,held=[],[]
    for orig in original['folds']:
        tick=time.perf_counter()
        i,origin=orig['fold'],pd.Timestamp(orig['origin'])
        model=prior.restore_model(base.read(source/'folds'/f'fold-{i}-C-model.json'))
        test=base.evaluation(frame,orig['origin'],bc['outer_snapshots'],bc['knowledge_boundary'])
        pred=model.risk(test)
        reproduce=prior.compare_metrics(base.metrics(test,pred),orig['C'],1e-8,f'C periodo {i}')
        dates=sorted(frame.loc[frame.y_6m.notna() & (frame.r6_end<origin),'snapshot_date'].unique())[-config['development_snapshots']:]
        dev=frame.loc[frame.snapshot_date.isin(dates)]
        if len(dates)!=config['development_snapshots'] or dev.r6_end.max()>=origin:
            raise RuntimeError('Desarrollo sin madurez anterior al origen.')
        base.log(f'Periodo {i}: búsqueda de cruces con cuatro variables sobre seis fotos previas.')
        candidates,selections=search(dev,model.risk(dev),model.features,config)
        evaluation,allocation=evaluate(test,pred,model.features,selections,config)
        reference=next(f for f in previous['folds'] if f['fold']==i)['evaluation']['C_Bcuts']
        differences={}
        for cap in ['20','30','40']:
            for key in ['capture_percent','coverage_percent','observed_percent','predicted_percent','group_mae_pp','group_snapshot_mae_pp']:
                differences[cap+'_'+key]=abs(evaluation['C_current']['scenarios'][cap]['metrics'][key]-reference['scenarios'][cap]['metrics'][key])
        if max(differences.values())>1e-8:
            raise RuntimeError('No se reproducen los cortes actuales de C.')
        record={'fold':i,'origin':orig['origin'],'first_snapshot':orig['first_snapshot'],'last_snapshot':orig['last_snapshot'],
                'latest_outcome':orig['latest_outcome'],'exposures':len(test),'people':test.person_key.nunique(),
                'development':{'first_snapshot':str(dev.snapshot_date.min().date()),'last_snapshot':str(dev.snapshot_date.max().date()),
                               'latest_outcome':str(dev.r6_end.max().date()),'exposures':len(dev)},
                'C_features':model.features,'candidate_count':len(candidates),'selections':selections,'evaluation':evaluation,
                'reproduction':reproduce,'current_cuts_maximum_difference':max(differences.values()),'elapsed_seconds':time.perf_counter()-tick}
        folds.append(record)
        held.append({'keys':test.person_key.to_numpy(),'y':test.y_6m.to_numpy(float),'allocations':allocation})
        write(out/'folds'/f'fold-{i}.json',record)
        write(out/'development-candidates'/f'fold-{i}.json',candidates)
        base.log(f'Periodo {i}: {len(candidates)} cruces; {record["elapsed_seconds"]:.1f} s; C + una variable: {selections["C_plus1"]["definition"]["name"]}.')
    base.log('Comparación pareada de captura y foto madura adicional.')
    intervals=uncertainty(held,config)
    aggregate=summarize(folds,intervals,config)
    ext=frame.loc[frame.snapshot_date==pd.Timestamp(config['extension_snapshot'])]
    if ext.empty or ext.y_6m.isna().any():
        raise RuntimeError('Foto adicional sin seguimiento.')
    ev,_=evaluate(ext,model.risk(ext),model.features,selections,config)
    unchanged=all(base.sha(ROOT/p)==digest for p,digest in before.items())
    if not unchanged:
        raise RuntimeError('Cambió un artefacto anterior.')
    result={'run_id':config['run_id'],'created_at':datetime.now(timezone.utc),'reporting_mode':'presentation',
            'query':bc['query'],'knowledge_boundary':bc['knowledge_boundary'],'folds':folds,'summary':aggregate,'intervals':intervals,
            'extension':{'snapshot':config['extension_snapshot'],'followup_end':str(ext.r6_end.max().date()),'people':len(ext),
                         'model_origin':original['folds'][-1]['origin'],'evaluation':ev},
            'load_seconds':load_seconds,'elapsed_seconds':time.perf_counter()-start,'hazard_refits':0,
            'employee_level_rows_persisted':False,'individual_scores_published':False,'qvoice_included':False}
    write(out/'results.json',result)
    write(out/'selected-groupings.json',{'origin':original['folds'][-1]['origin'],'selections':selections,
                                      'model':config['source_c']+'/trained-model/model-c.json','minimum_people_each_snapshot':300})
    write(out/'preservation.json',{'unchanged':True,'files':before})
    write(out/'analysis-checks.json',{'population_reproduced':True,'current_cuts_reproduced':True,
          'models_reproduced':[f['reproduction'] for f in folds],'selection_before_external_outcomes':True,
          'capacity_checked_each_snapshot':True,'capture_reconciled_to_rows_in_memory':True,
          'same_partition_comparator':True,'prior_artifacts_unchanged':True,'hazard_refits':0,'rows_persisted':False})
    write(out/'completed.json',{'status':'completed_analysis','seconds':result['elapsed_seconds']})
    write(out/'manifest.json',{'run_id':config['run_id'],'status':'completed_analysis','reporting_mode':'presentation',
          'authorization':config['authorization'],'employee_level_rows_persisted':False,'individual_scores_published':False,
          'salt_persisted':False,'files':{str(p.relative_to(out)):base.sha(p) for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'}})
    base.log(f'Agrupaciones de cuatro variables terminadas en {result["elapsed_seconds"]:.1f} s.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=DEFAULT)
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        run(args.config.resolve())
