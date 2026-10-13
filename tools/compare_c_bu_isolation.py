"""Comparación focalizada C+BU con/sin QVoice. Sólo modelos y agregados a disco."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys
import time
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import engineering_julia_rh_review as r
import julia_review_statistics as stats

NAMES = ['C_archived', 'C_refit', 'C_BU', 'CQ', 'C_BU_Q', 'FQ', 'FQ_BU_L3']
PAIRS = [('C_BU', 'C_refit'), ('C_BU', 'C_archived'), ('C_BU', 'CQ'),
         ('C_BU_Q', 'C_BU'), ('C_BU_Q', 'CQ'), ('FQ_BU_L3', 'C_BU_Q'),
         ('FQ_BU_L3', 'C_BU'), ('C_refit', 'C_archived')]
LABELS = {'C_archived':'C histórico', 'C_refit':'C reajustado al corte',
          'C_BU':'C + BU L3 (sin QVoice)', 'CQ':'CQ',
          'C_BU_Q':'C + BU L3 + QVoice', 'FQ':'C + ciudad + QVoice',
          'FQ_BU_L3':'C + ciudad + BU L3 + QVoice'}


def save_rh(out, period, name, model):
    artifact = {'base': (model.model if isinstance(model, r.bu.PooledModel) else model).artifact(),
                'pool_keep': model.pool.keep if isinstance(model, r.bu.PooledModel) else None,
                'cutoff': period['origin'], 'qvoice': False, 'employee_level_rows_persisted': False}
    r.write(out/'models'/f'{period["id"]}-{name}.json', artifact)
    restored = r.cq.prior.restore_model(artifact['base'])
    if artifact['pool_keep'] is not None:
        restored = r.bu.PooledModel(restored, r.bu.BUPool(artifact['pool_keep']))
    return restored


def fmt(v, scale=1):
    return f'{v*scale:.4f}'


def report(result, out):
    s = result['summary']
    lines = ['# C + BU L3 sin QVoice: comparación específica', '',
             'Modo `presentation`. Ingeniería, mismas personas y fotos en todos los modelos. '
             'Agosto–diciembre 2025 y enero–febrero 2026, igual peso entre periodos. '
             'Salida voluntaria a seis meses; ventanas superpuestas.', '',
             '| Modelo | Log-loss ×1000 ↓ | Brier ×1000 ↓ | Captura 30% ↑ | Error grupo-mes, pp ↓ |',
             '|---|---:|---:|---:|---:|']
    for n in NAMES:
        m = s[n]['30']
        lines.append(f'| {LABELS[n]} | {fmt(m["log_loss"],1000)} | {fmt(m["brier"],1000)} | {fmt(m["capture_percent"])}% | {fmt(m["group_snapshot_mae_pp"])} |')
    lines += ['', '## Diferencias pareadas', '',
              'Candidato menos referencia; valores negativos favorecen pérdidas/error, positivos favorecen captura. '
              'IC95 con 500 remuestreos de personas compartidos entre periodos y modelos; modelos y prioridades fijos.', '',
              '| Contraste | Δ log-loss ×1000 [IC95] | Δ captura, pp [IC95] | Δ error, pp [IC95] |',
              '|---|---:|---:|---:|']
    for a,b in PAIRS:
        d = result['differences'][a+'_minus_'+b]['30']
        def cell(k, scale=1):
            v=d[k]
            return f'{fmt(v["difference"],scale)} [{fmt(v["ci95"][0],scale)}, {fmt(v["ci95"][1],scale)}]'
        lines.append(f'| {LABELS[a]} − {LABELS[b]} | {cell("log_loss",1000)} | {cell("capture_percent")} | {cell("group_snapshot_mae_pp")} |')
    lines += ['', '## Por periodo', '', '| Periodo | Modelo | Log-loss ×1000 | Brier ×1000 | Captura 30% | Error, pp |', '|---|---|---:|---:|---:|---:|']
    for block in result['periods']:
        for n in NAMES:
            m=block['models'][n]['capacities']['30']['metrics']
            lines.append(f'| {block["period"]["id"]} | {LABELS[n]} | {fmt(m["log_loss"],1000)} | {fmt(m["brier"],1000)} | {fmt(m["capture_percent"])}% | {fmt(m["group_snapshot_mae_pp"])} |')
    lines += ['', '## Interpretación y límites', '',
        'La ronda v7 incluyó QVoice y no conservó C + BU sin encuesta. Esta ejecución lo evalúa '
        'explícitamente y guarda sus coeficientes. C reajustado usa exactamente las fechas, estructura '
        'y penalización del candidato: el contraste C + BU menos C reajustado separa BU de la actualización temporal.', '',
        'CQ conserva en enero su base RH de agosto. Compararlo con los candidatos actualizados es válido '
        'como comparación de estimadores completos, pero no aísla una sola variable. La comparación '
        'C + BU + QVoice frente a FQ + BU sí comparte los cortes RH y la selección QVoice.', '',
        'Las capacidades 10/20/30 y sus alternativas de incluir/excluir el grupo límite están en results.json. '
        'Los grupos mantienen mínimo 300 y la misma definición; BU se incorpora como predictor. '
        'No se publican scores ni filas individuales. Los promedios de tasas se basan en exposiciones '
        'persona-mes y no deben interpretarse como salidas únicas de toda la ventana.', '',
        'Conclusiones retrospectivas y condicionadas a elecciones previas. IOS y la publicación real '
        'de QVoice no tienen disponibilidad histórica acreditada. No se cambian scores de assessment '
        'ni se adopta otro modelo automáticamente.', '',
        'Reproducción: `.venv/Scripts/python.exe -B tools/compare_c_bu_isolation.py '
        '--config config/engineering_c_bu_isolation_20261013.json` usando otra carpeta de salida. '
        'Fuente SQL, hashes, cortes, tiempos, parámetros y verificaciones quedan en esta carpeta.']
    (out/'informe.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def run(path):
    started=time.perf_counter(); spec=r.read(path); out=ROOT/spec['output']
    if out.exists(): raise RuntimeError('Salida existente: use otra carpeta.')
    out.mkdir(parents=True)
    ref=ROOT/spec['reference_run']; source=r.read(ROOT/spec['source_config'])
    cconfig=r.read(ROOT/source['c_config'])
    manifest={'run_id':spec['run_id'],'reporting_mode':'presentation',
              'authorization':spec['authorization'],'employee_level_rows_persisted':False,
              'individual_scores_published':False,'started_at':datetime.now(timezone.utc).isoformat(),
              'status':'running','fits':{'base':0,'q':0}}
    r.write(out/'manifest.json',manifest); r.write(out/'frozen-config.json',spec)
    source_paths=[path,Path(__file__),ROOT/spec['source_config'],ROOT/source['base_query'],
                  ROOT/source['c_config'],ROOT/source['source_c_config'],ROOT/source['loader_config'],
                  ROOT/'tools/julia_review_statistics.py',ROOT/'tools/engineering_bu_l3_experiment.py',
                  ROOT/'tools/b_incremental_data.py',ROOT/'tools/engineering_julia_rh_review.py']
    for p in source['periods']:
        source_paths += [ref/'models'/f'{p["id"]}-{n}.json' for n in r.NAMES]
    hashes={p.relative_to(ROOT).as_posix():r.sha(p) for p in source_paths}
    for p in source_paths:
        dest=out/'source'/p.relative_to(ROOT); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dest)
    r.write(out/'source-hashes.json',hashes)
    r.log('Auditoría enfocada del mapping BU antes de comparar.')
    r.bu.copy_evidence(source,out)
    audit=r.bu.audit_bu_l3(source,out)
    assert audit['unmatched_rate_percent']<=0.1
    r.write(out/'bu-mapping-acceptance.json',{'outcome':'pass','unmatched_rate_percent':audit['unmatched_rate_percent'],
        'maximum_unmatched_rate_percent':0.1,'duplicate_valid_matches':audit['metrics']['duplicate_valid_matches'],
        'multi_bu_valid_matches':audit['metrics']['multi_bu_valid_matches'],'assessment_score_changed':False})
    loader=r.bu.loader_config(source,out)
    r.log('Carga compartida RH/QVoice exclusivamente en RAM; sin búsqueda de variables.')
    frame,qframe=r.data.load(loader,out)
    alltest=pd.concat([r.bu.test_frame(qframe,p,loader['knowledge_boundary']) for p in source['periods']],ignore_index=True)
    assert not alltest.duplicated(['person_key','snapshot_date']).any()
    boot=stats.Bootstrap(alltest.person_key.to_numpy(),spec['bootstrap_repetitions'],spec['seed'])
    reference=r.read(ref/'results.json'); periods=[]; reps_all=[]; offset=0; checks=[]
    for period in source['periods']:
        tick=time.perf_counter(); pid=period['id']; origin=period['origin']
        test=r.bu.test_frame(qframe,period,loader['knowledge_boundary']).reset_index(drop=True)
        indices=np.arange(offset,offset+len(test)); offset+=len(test); y=test.y_6m.to_numpy(float)
        assert test.person_key.nunique()>=30 and test.loc[test.y_6m==1,'person_key'].nunique()>=30
        train=r.c.train_before(frame,origin)
        assert train.label_end.max()<=pd.Timestamp(origin)
        train_last=str(train.label_end.max().date()); del train
        old=r.read(ref/'models'/f'{pid}-CQ.json'); base,q=r.restore(old)
        predictions={'C_archived':base.risk(test)}
        for n,additions in [('C_refit',[]),('C_BU',['bu_l3'])]:
            r.log(f'{pid}: ajuste {n}, variables y L2 fijos.')
            model=r.bu.fit_c_addition(frame,origin,base,additions,cconfig)
            assert not set(spec['excluded_predictors'])&set(model.features)
            manifest['fits']['base']+=1
            restored=save_rh(out,period,n,model)
            predictions[n]=model.risk(test)
            assert np.allclose(predictions[n],restored.risk(test),atol=1e-12,rtol=0)
            if n=='C_BU':
                r.log(f'{pid}: corrección QVoice de C + BU con selección archivada.')
                fitted=r.bu.fit_q(model,qframe,origin,old['selected']); manifest['fits']['q']+=1
                artifact=r.export_model(model,fitted,old['selected'],origin,origin,'C+BU ajustado en este run')
                r.write(out/'models'/f'{pid}-C_BU_Q.json',artifact)
                predictions['C_BU_Q']=r.bu.risk_with_correction(model,test,r.bu.q_correction(fitted,test))
                mr,qr=r.restore(artifact)
                assert np.allclose(predictions['C_BU_Q'],r.bu.risk_with_correction(mr,test,r.bu.q_correction(qr,test)),atol=1e-12,rtol=0)
            r.write(out/'manifest.json',manifest)
        for n in r.NAMES:
            model,q=r.restore(r.read(ref/'models'/f'{pid}-{n}.json'))
            predictions[n]=r.bu.risk_with_correction(model,test,r.bu.q_correction(q,test))
        keys=r.cq.groups.cut_keys(test,[])
        parent=keys[['antiguedad','salidas_equipo','nivel']].agg(' · '.join,axis=1).to_numpy()
        block={'period':period,'people':int(test.person_key.nunique()),'observations':len(test),
               'event_exposures':int(y.sum()),'distinct_people_with_event':int(test.loc[test.y_6m==1,'person_key'].nunique()),
               'last_training_label':train_last,'CQ_base_cutoff':old['base_cutoff'],'models':{}}
        archive=next(x for x in reference['periods'] if x['period']['id']==pid)
        assert all(block[k]==archive[k] for k in ['people','observations','event_exposures','distinct_people_with_event'])
        per_reps={}
        for n in NAMES:
            p=predictions[n]; stats_values=r.c.metrics(test,p); caps={}; per_reps[n]={}
            boot.metric_cache.clear()
            for cap in spec['capacities']:
                k=str(round(100*cap)); s=r.structure(test,p,parent,cap)
                met,reps=stats.metrics(y,p,s['weights'],s['cells'],boot,indices)
                assert abs(met['coverage_percent']-100*cap)<1e-8
                caps[k]={'metrics':met,'ci95':{z:stats.interval(v) for z,v in reps.items()},'monthly':s['monthly']}
                for boundary in ['low','high']:
                    caps[k][boundary]=stats.metrics(y,p,s[boundary],s['cells'],boot,indices)[0]
                per_reps[n][k]=reps
            block['models'][n]={'capacities':caps,'ranking':stats_values}
            if n in r.NAMES:
                errors={k:abs(caps['30']['metrics'][k]-archive['models'][n]['capacities']['30']['metrics'][k]) for k in ['log_loss','brier','capture_percent','group_snapshot_mae_pp']}
                assert max(errors.values())<1e-8
                checks.append({'period':pid,'model':n,'archival_metric_abs_difference':errors})
        block['elapsed_seconds']=time.perf_counter()-tick; periods.append(block); reps_all.append(per_reps)
        r.write(out/'periods'/f'{pid}.json',block)
        r.log(f'{pid} terminado; población, serialización y referentes verificados.')
    summary={n:{k:{m:float(np.mean([b['models'][n]['capacities'][k]['metrics'][m] for b in periods]))
                     for m in periods[0]['models'][n]['capacities'][k]['metrics']}
                for k in ['10','20','30']} for n in NAMES}
    differences={}
    for a,b in PAIRS:
        differences[a+'_minus_'+b]={}
        for k in ['10','20','30']:
            differences[a+'_minus_'+b][k]={m:{'difference':summary[a][k][m]-summary[b][k][m],
                'ci95':stats.interval(sum((rep[a][k][m]-rep[b][k][m])*.5 for rep in reps_all))}
                for m in reps_all[0][a][k]}
    result={'reporting_mode':'presentation','employee_level_rows_persisted':False,
            'authorization':spec['authorization'],'period_weights':spec['period_weights'],
            'labels':LABELS,'summary':summary,'periods':periods,'differences':differences,
            'source_query':source['base_query'],'query_executed_at':manifest['started_at'],
            'bootstrap':{'repetitions':500,'unit':'person','shared_across_models_and_periods':True,
                         'conditional_on_fitted_models_and_fixed_priorities':True}}
    r.write(out/'results.json',result); report(result,out)
    assert manifest['fits']['base']<=spec['maximum_base_fits'] and manifest['fits']['q']<=spec['maximum_q_fits']
    r.write(out/'verification.json',{'checks':checks,'same_population_dates_outcomes':True,
        'capacity_conserved':True,'saved_models_reproduced':True,'past_labels_only':True,
        'no_job_family_detail':True,'base_fits':manifest['fits']['base'],'q_fits':manifest['fits']['q'],
        'all_source_hashes_unchanged':all(r.sha(ROOT/p)==v for p,v in hashes.items()),
        'reporting_mode':'presentation','employee_level_rows_persisted':False})
    manifest.update(status='completed_retrospective_comparison',elapsed_seconds=time.perf_counter()-started,
                    finished_at=datetime.now(timezone.utc).isoformat())
    r.write(out/'manifest.json',manifest); r.log('Comparación C + BU terminada; sólo agregados y modelos guardados.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--config',type=Path,default=ROOT/'config/engineering_c_bu_isolation_20261013.json')
    args=parser.parse_args(); sys.stdout.reconfigure(encoding='utf-8')
    with threadpool_limits(limits=1): run(args.config.resolve())
