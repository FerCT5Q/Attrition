"""Orquesta la evaluación completa de B incremental y congela sólo agregados."""
from __future__ import annotations

from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import shutil
import time

import numpy as np
import pandas as pd

import engineering_b_incremental as inc
import engineering_model_c as base
import b_incremental_data as data
import b_incremental_qvoice as q

ROOT = base.ROOT


def old_hashes():
    paths = [ROOT/'output/analysis/engineering/20261003/playbook-tenure-confirmation-v1/confirmation-results.json']
    for directory in ['model-c-v2','model-c-plus-qvoice-v1','qvoice-model-b-calibrated-v1']:
        folder = ROOT/'output/analysis/engineering/20261008'/directory/'trained-model'
        if folder.exists():
            paths.extend(folder.rglob('*.json'))
    return {p.relative_to(ROOT).as_posix():base.sha(p) for p in paths if p.is_file()}


def evaluation_frame(frame,period,config):
    result = frame.loc[(frame.snapshot_date>=pd.Timestamp(period['origin'])) &
                       (frame.snapshot_date<=pd.Timestamp(period['end'])) & frame.y_6m.notna() &
                       (frame.r6_end<=pd.Timestamp(config['knowledge_boundary']))]
    if result.snapshot_date.nunique()!=period['snapshots']:
        raise RuntimeError('El periodo externo no tiene el seguimiento declarado.')
    return result


def hold(frame,prediction,config):
    evaluator = inc.Evaluation(frame,config)
    g = evaluator.grouped(prediction)
    w = g.allocation(config['primary_capacity_fraction'])[0].ravel()[g.cells]
    return {'prediction':prediction,'weights':w}


def verify_roundtrip(model,frame,p):
    if isinstance(model,inc.HRModel):
        restored = inc.HRModel.restore(model.artifact()).risk(frame)
    else:
        restored = q.predict_saved(model,frame)
    difference = float(np.max(np.abs(restored-p)))
    if difference>1e-10:
        raise RuntimeError(f'El artefacto exportado no reproduce las predicciones en RAM; diferencia máxima {difference:.6g}.')
    return difference


def compare_period(frame,qframe,period,config,out,held):
    name,cutoff = period['id'],period['origin']
    selection = inc.select_hr(frame,cutoff,config,out/'selection'/f'{name}-hr.json')
    test = evaluation_frame(frame,period,config)
    train = base.train_before(frame,cutoff)
    context = inc.HRContext(train,test,config,cutoff)
    l2 = selection['baseline']['l2']
    b,pb,_ = context.fit([],l2)
    context.evaluation.set_reference(pb)
    selected,ps,_ = context.fit(selection['winner']['additions'],l2)
    metrics = {'B':context.evaluation.score(pb,True),'B_RH':context.evaluation.score(ps,True)}
    inc.write(out/'models'/f'{name}-B.json',b.artifact())
    inc.write(out/'models'/f'{name}-B-RH.json',selected.artifact())
    roundtrips = {'B':verify_roundtrip(b,test,pb),'B_RH':verify_roundtrip(selected,test,ps)}
    candidates = []
    for i,feature in enumerate(inc.hr_candidates(config),1):
        row = {'feature':feature,'family':'RH','period':name}
        try:
            fitted,p,_ = context.fit([feature],l2)
            row.update(status='ok',metrics=context.evaluation.score(p),
                       training_support=context.availability[feature])
        except (RuntimeError,np.linalg.LinAlgError) as error:
            row.update(status='failed',reason=str(error))
        candidates.append(row)
        if i%5==0:
            base.log(f'Externo {name}: {i}/{len(inc.hr_candidates(config))} incorporaciones RH evaluadas.')
    h = {'period':name,'frame':test[['person_key','snapshot_date','y_6m']].copy(),
         'models':{'B':hold(test,pb,config),'B_RH':hold(test,ps,config)}}
    record = {'period':period,'hr_selection':selection['winner']['additions'],'hr_l2':l2,
              'metrics':metrics,'candidates':candidates,'roundtrip_maximum_difference':roundtrips,
              'selection_file':f'selection/{name}-hr.json'}
    del context,train
    gc.collect()
    if name in config['qvoice']['period_ids']:
        qt = evaluation_frame(qframe,period,config)
        if len(qt)!=len(test) or not np.array_equal(qt.person_key.to_numpy(),test.person_key.to_numpy()):
            # La construcción conserva orden, y se exige para los intervalos pareados.
            raise RuntimeError('Las poblaciones de QVoice y RH no coinciden en el periodo externo.')
        qtrain = base.train_before(qframe,cutoff)
        record['qvoice_selections'] = {}
        for anchor,hr in [('B',b),('B_RH',selected)]:
            additions = [] if anchor=='B' else selection['winner']['additions']
            qs = q.select(qframe,frame,cutoff,additions,l2,anchor,config,out/'selection'/f'{name}-{anchor}-qvoice.json')
            qcontext = q.Context(qtrain,qt,hr,config)
            refresh_spec = qs['intercept_control']
            refresh,pr = q.refit(qcontext,refresh_spec)
            metrics[anchor+'_refresh'] = qcontext.evaluation.score(pr,True)
            fitted,p = q.refit(qcontext,qs['winner'])
            alias = anchor+'_Q'
            metrics[alias] = qcontext.evaluation.score(p,True)
            exported = q.artifact(hr,fitted,qs['winner'],cutoff)
            inc.write(out/'models'/f'{name}-{alias}.json',exported)
            roundtrips[alias] = verify_roundtrip(exported,qt,p)
            h['models'][alias] = hold(qt,p,config)
            h['models'][anchor+'_refresh'] = hold(qt,pr,config)
            record['qvoice_selections'][anchor] = {'features':qs['winner']['additions'],'kind':qs['winner']['kind'],
                                                  'selection_mode':qs['split']['selection_mode']}
            for i,spec in enumerate((r for r in qs['trials'] if r.get('stage')=='single'),1):
                row = {'feature':spec['additions'][0],'family':'QVoice','anchor':anchor,'period':name}
                if spec['status']!='ok':
                    row.update(status='failed',reason='No convergió la selección interna.')
                else:
                    try:
                        fitted,p = q.refit(qcontext,spec)
                        row.update(status='ok',metrics=qcontext.evaluation.score(p),l2=spec['l2'])
                        ac = spec.get('availability_control')
                        if ac:
                            _,pa = q.refit(qcontext,ac)
                            row['matched_availability_metrics'] = qcontext.evaluation.score(pa)
                    except (RuntimeError,np.linalg.LinAlgError) as error:
                        row.update(status='failed',reason=str(error))
                candidates.append(row)
                if i%10==0:
                    base.log(f'Externo {name} sobre {anchor}: {i} incorporaciones QVoice evaluadas.')
            del qcontext
            gc.collect()
    held.append(h)
    inc.write(out/'periods'/f'{name}.json',record)
    base.log(f'Periodo {name} completo. B: {metrics["B"]["capture_percent"]:.1f}% de captura; extensión RH: {metrics["B_RH"]["capture_percent"]:.1f}%.')
    return record


def paired_intervals(held,left,right,config):
    usable = [h for h in held if left in h['models'] and right in h['models']]
    if not usable:
        return None
    keys = np.concatenate([h['frame'].person_key.to_numpy() for h in usable])
    inverse,unique = pd.factorize(keys,sort=False)
    counts,events,loss,caloss,lcap,rcap = [],[],[],[],[],[]
    start = 0
    for h in usable:
        frame = h['frame']
        codes = inverse[start:start+len(frame)]
        start += len(frame)
        y = frame.y_6m.to_numpy(float)
        lp,rp = h['models'][left]['prediction'],h['models'][right]['prediction']
        ll,rl = base.losses(y,lp),base.losses(y,rp)
        def bins(v):
            return np.bincount(codes,weights=v,minlength=len(unique))
        counts.append(bins(np.ones(len(y))))
        events.append(bins(y))
        loss.append(bins(ll['log_loss']-rl['log_loss']))
        caloss.append(bins(ll['brier_score']-rl['brier_score']))
        lcap.append(bins(y*h['models'][left]['weights']))
        rcap.append(bins(y*h['models'][right]['weights']))
    matrices = [np.asarray(a) for a in [counts,events,loss,caloss,lcap,rcap]]
    rng = np.random.default_rng(config['seed'])
    draws = []
    for _ in range(config['bootstrap_repetitions']):
        w = rng.multinomial(len(unique),np.full(len(unique),1/len(unique)))
        n,e,l,b,lc,rc = [a@w for a in matrices]
        if np.any(n<=0) or np.any(e<=0):
            continue
        draws.append([np.mean(l/n),np.mean(b/n),np.mean(100*(lc-rc)/e)])
    values = np.asarray(draws)
    return {'left':left,'right':right,'periods':[h['period'] for h in usable],
            'method':'Bootstrap pareado por persona; selección de variables y grupos fija por periodo, pesos iguales por periodo.',
            'repetitions':len(draws),'log_loss_delta':np.quantile(values[:,0],[.025,.975]).tolist(),
            'brier_delta':np.quantile(values[:,1],[.025,.975]).tolist(),
            'capture_delta_pp':np.quantile(values[:,2],[.025,.975]).tolist()}


def mean_metrics(periods,model,period_ids=None):
    selected = [r for r in periods if model in r['metrics'] and (period_ids is None or r['period']['id'] in period_ids)]
    fields = ['log_loss','brier_score','pr_auc','lift_at_10_percent','observed_percent','predicted_percent',
              'common_group_snapshot_mae_pp','capture_percent','priority_group_snapshot_mae_pp','on_B_selection_mae_pp',
              'individual_capacity_capture_percent','individual_minus_group_capture_pp']
    return {'periods':[r['period']['id'] for r in selected],
            **{f:float(np.mean([r['metrics'][model][f] for r in selected])) for f in fields if all(f in r['metrics'][model] for r in selected)}}


def final_models(frame,qframe,config,out):
    cutoff = config['knowledge_boundary']
    selection = inc.select_hr(frame,cutoff,config,out/'selection/final-hr.json')
    l2 = selection['baseline']['l2']
    b = inc.fit_hr(frame,cutoff,[],l2,config)
    selected = inc.fit_hr(frame,cutoff,selection['winner']['additions'],l2,config)
    inc.write(out/'models/final-B.json',b.artifact())
    inc.write(out/'models/final-B-RH.json',selected.artifact())
    summary = {'cutoff':cutoff,'hr_additions':selection['winner']['additions'],'l2':l2,
               'evaluation':'No se evalúan los coeficientes finales sobre periodos anteriores como si fueran externos.','qvoice':{}}
    train = base.train_before(qframe,cutoff)
    last = qframe.loc[qframe.snapshot_date==qframe.snapshot_date.max()]
    for anchor,hr in [('B',b),('B_RH',selected)]:
        additions = [] if anchor=='B' else selection['winner']['additions']
        qs = q.select(qframe,frame,cutoff,additions,l2,anchor,config,out/'selection'/f'final-{anchor}-qvoice.json')
        context = q.Context(train,last,hr,config,mode='monthly_fallback')
        correction,_ = q.refit(context,qs['winner'])
        exported = q.artifact(hr,correction,qs['winner'],cutoff)
        # Verificación de serialización con probabilidades, sin usar outcomes de la última foto.
        prediction = q.predict_saved(exported,last)
        if not np.isfinite(prediction).all():
            raise RuntimeError('El modelo final no produce probabilidades finitas.')
        inc.write(out/'models'/f'final-{anchor}-Q.json',exported)
        summary['qvoice'][anchor] = {'features':qs['winner']['additions'],'kind':qs['winner']['kind'],
                                     'selection_mode':qs['split']['selection_mode']}
        del context
        gc.collect()
    return summary


def run(path):
    path = Path(path).resolve()
    started = time.perf_counter()
    config = base.read(path)
    out = ROOT/config['output']
    if (out/'frozen-config.json').exists():
        raise RuntimeError('El ajuste ya se inició; conservarlo y usar una nueva ejecución para repetir.')
    before = old_hashes()
    inc.write(out/'preserved-models-before.json',before)
    inc.write(out/'frozen-config.json',config)
    sources = [path,ROOT/config['plan'],ROOT/config['input_contracts']]
    sources += [ROOT/config[k] for k in ['base_query','history_query','pending_query','source_qvoice_config']]
    sources += [ROOT/b['query'] for b in config.get('extra_hr_queries',[])]
    sources += [ROOT/p for p in config.get('additional_reproducibility_sources',[])]
    sources += [ROOT/'tools'/f for f in ['engineering_b_incremental.py','run_engineering_b_incremental.py',
                                      'b_incremental_data.py','b_incremental_qvoice.py','build_b_incremental_report.py']]
    sources += [ROOT/'tools'/f for f in ['engineering_model_c.py','engineering_model_c_fast.py',
        'engineering_c_group_selection.py','qvoice_horizon_calibration.py','qvoice_model_data.py',
        'qvoice_model_experiment.py','qvoice_model_validation.py']]
    sources += [ROOT/'tests/test_b_incremental.py',ROOT/config['qvoice']['annual_lag_policy']]
    source_hashes = {p.relative_to(ROOT).as_posix():base.sha(p) for p in sources}
    inc.write(out/'source-hashes.json',source_hashes)
    inc.write(out/'manifest.json',{'run_id':config['run_id'],'status':'running','reporting_mode':'presentation',
                                  'started_at':datetime.now(timezone.utc).isoformat(),'authorization':config['authorization'],
                                  'employee_level_rows_persisted':False,'individual_scores_published':False})
    frame,qframe = data.load(config,out)
    held,periods = [],[]
    for period in config['periods']:
        periods.append(compare_period(frame,qframe,period,config,out,held))
    intervals = [paired_intervals(held,a,b,config) for a,b in [('B_RH','B'),('B_Q','B'),
                 ('B_RH_Q','B'),('B_Q','B_refresh'),('B_RH_Q','B_RH_refresh')]]
    summaries = {'RH':{name:mean_metrics(periods,name) for name in ['B','B_RH']},
                 'QVoice':{name:mean_metrics(periods,name,config['qvoice']['period_ids'])
                           for name in ['B','B_RH','B_refresh','B_RH_refresh','B_Q','B_RH_Q']}}
    final = final_models(frame,qframe,config,out)
    result = {'run_id':config['run_id'],'reporting_mode':'presentation','periods':periods,
              'summary':summaries,'intervals':intervals,'final':final,
              'mandatory_features':list(inc.B_TERMS),'hr_candidates':inc.hr_candidates(config),
              'qvoice_candidates':inc.q_candidates(config),'employee_level_rows_persisted':False,
              'individual_scores_published':False,'external_outcomes_used_for_selection':False,
              'limitations':['Evaluación retrospectiva en años explorados previamente; requiere confirmación prospectiva.',
                             'Shortlist interna de seis para pares y tríos; no es el óptimo global de todas las combinaciones.',
                             'QVoice tiene dos periodos externos; el primer corte requiere validación mensual interna.',
                             'Tiempo en perfil de puesto aparece desde noviembre de 2025 y no tiene historia interna suficiente.',
                             'No se reconstruye fecha real de publicación QVoice: se aplica la política anual aprobada.',
                             'Career cambia de redacción en 2024; su transporte es exploratorio.',
                             'Los predictores RH y QVoice se mantienen constantes al calcular los seis meses, salvo calendario.']
                             +config.get('preparation_limitations',[])}
    inc.write(out/'results.json',result)
    from build_b_incremental_report import build
    build(result,config,out)
    after = old_hashes()
    if before!=after:
        raise RuntimeError('Cambió un artefacto anterior durante el experimento.')
    if any(base.sha(ROOT/p)!=digest for p,digest in source_hashes.items()):
        raise RuntimeError('Cambió una fuente de ejecución mientras se ajustaba.')
    inc.write(out/'preserved-models-after.json',after)
    verification = {'mandatory_features_preserved':True,'previous_models_unchanged':True,
                    'external_outcomes_used_for_selection':False,'artifact_roundtrips_pass':True,
                    'employee_level_rows_persisted':False,'individual_scores_published':False}
    inc.write(out/'verification.json',verification)
    inc.write(out/'manifest.json',{'run_id':config['run_id'],'status':'completed_experimental',
        'reporting_mode':'presentation','completed_at':datetime.now(timezone.utc).isoformat(),
        'elapsed_seconds':time.perf_counter()-started,'authorization':config['authorization'],
        'employee_level_rows_persisted':False,'individual_scores_published':False,'salt_persisted':False,
        'source_hashes':source_hashes,'files':{p.relative_to(out).as_posix():base.sha(p) for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'}})
    base.log('B incremental completo; sólo resultados agregados y modelos experimentales guardados.')
