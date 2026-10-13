"""Completa captura por disponibilidad y fichas desde modelos guardados, sin ajustes."""
from __future__ import annotations

from datetime import datetime,timezone
from pathlib import Path
import secrets
import sys
import time
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import engineering_julia_rh_review as review
import julia_review_statistics as stats


def unique_group_events(source,out):
    """Agregado independiente: eventos persona-fecha; mismos cortes de las fichas.

    Aceptación: personas y exposiciones con evento coinciden con RAM en cada
    celda publicada. Se publican >=30 personas con evento; al menos dos celdas
    ocultas por mes si existe una restringida. No se devuelven llaves.
    """
    base=(ROOT/source['base_query']).read_text(encoding='utf-8')
    prefix=base.split('\nSELECT\n  f.snapshot_date,')[0]
    prefix=prefix.replace('__PERIOD_START__','2025-08-01').replace('__PERIOD_END__','2026-02-28')
    sql=prefix+''', grouped AS (
 SELECT f.employee_id,f.snapshot_date,
 CASE WHEN f.tenure_months IS NULL THEN 'sin dato'
 WHEN f.tenure_months<12 THEN '<1 año' WHEN f.tenure_months<24 THEN '1-2 años'
 WHEN f.tenure_months<36 THEN '2-3 años' WHEN f.tenure_months<60 THEN '3-5 años'
 WHEN f.tenure_months<120 THEN '5-10 años' ELSE '10+ años' END
 || ' · ' || CASE WHEN f.manager_id IS NULL THEN 'sin dato'
 WHEN COALESCE(f.team_exit_count,0)=0 THEN 'sin salidas' ELSE 'con salidas' END
 || ' · ' || CASE WHEN SPLIT_PART(f.level_grouped,' - ',1) IN ('1','2','3') THEN 'alto'
 WHEN SPLIT_PART(f.level_grouped,' - ',1) IN ('5','6') THEN 'medio'
 WHEN SPLIT_PART(f.level_grouped,' - ',1) IN ('7','8') THEN 'entrada' ELSE 'otro' END AS parent
 FROM features f
), counts AS (
 SELECT g.snapshot_date,g.parent,COUNT(DISTINCT g.employee_id) AS people,
 COUNT(DISTINCT CASE WHEN v.term_date IS NOT NULL THEN g.employee_id END) AS event_exposures,
 COUNT(DISTINCT CASE WHEN v.term_date IS NOT NULL THEN g.employee_id::VARCHAR || '|' || v.term_date::VARCHAR END) AS unique_exit_events
 FROM grouped g LEFT JOIN voluntary_events v ON v.employee_id=g.employee_id
 AND v.term_date>g.snapshot_date AND v.term_date<=DATEADD(month,6,g.snapshot_date)
 GROUP BY 1,2
), flags AS (
 SELECT snapshot_date,parent,people,event_exposures,unique_exit_events,
 CASE WHEN people<30 OR event_exposures<30 THEN 1 ELSE 0 END AS hidden
 FROM counts
), complement AS (
 SELECT snapshot_date,parent,people,event_exposures,unique_exit_events,hidden,
 SUM(hidden) OVER(PARTITION BY snapshot_date) AS hidden_cells,
 ROW_NUMBER() OVER(PARTITION BY snapshot_date,hidden ORDER BY event_exposures,parent) AS safety_order
 FROM flags
)
SELECT snapshot_date,parent,people,event_exposures,unique_exit_events
FROM complement WHERE hidden=0 AND NOT(hidden_cells=1 AND safety_order=1)
ORDER BY snapshot_date,parent
'''
    path=ROOT/'queries/audits/julia_review_unique_group_events_20261012.sql'
    path.write_text('/* presentation: salida persona-fecha distinta, por grupo/foto. Regla: >=30 personas/eventos; supresión complementaria. */\n'+sql,encoding='utf-8')
    return review.bu.run_aggregate_query(path,out,'unique-group-events',1000)


def main(config_path):
    started=time.perf_counter();spec=review.read(config_path);out=ROOT/spec['output']
    results=review.read(out/'results.json');source=review.read(ROOT/spec['source_config'])
    events=unique_group_events(source,out)
    event_map={str(r['snapshot_date'])+' | '+r['parent']:r for r in events['rows']}
    loader=review.bu.loader_config(source,out)
    # Lectura enfocada sólo de evaluación; necesaria para captura por estado y fichas
    # que los resúmenes principales no permiten reconstruir. Cero búsquedas/ajustes.
    loader['training_start']='2025-08-01';loader['knowledge_boundary']='2026-09-07'
    review.data.check_authorization(loader)
    config=review.read(ROOT/source['source_c_config']);raw=review.c.raw_features(config)
    expected={'snapshot_date','person_key','label_end','y_next','y_6m','company_tenure_band','tenure_julia_band',
              'same_episode_2024','same_episode_2025','same_episode_2026'}|set(raw)
    salt=secrets.token_hex(32)
    review.log('Suplemento: sólo fechas de evaluación, cero ajustes de modelos.')
    read_window=dict(loader,knowledge_boundary='2026-02-28')
    frame=review.data.read_frame(source['base_query'],expected,raw,read_window,salt,'Evaluación focalizada')
    frame=frame.loc[((frame.snapshot_date>='2025-08-01')&(frame.snapshot_date<='2025-12-31'))|
                    ((frame.snapshot_date>='2026-01-01')&(frame.snapshot_date<='2026-02-28'))].copy().reset_index(drop=True)
    frame['label_end']=pd.to_datetime(frame.label_end);frame['r6_end']=frame.snapshot_date+pd.DateOffset(months=6)
    frame['calendar_month']=frame.snapshot_date.dt.month.astype(str).astype('category')
    qconfig=review.data.load_config(ROOT/loader['source_qvoice_config'])
    metadata=review.read(ROOT/loader['source_qvoice_metadata'])
    models={(p['id'],name):review.read(out/'models'/f'{p["id"]}-{name}.json') for p in source['periods'] for name in review.NAMES}
    features=sorted(set(f for a in models.values() for f in a['selected']['features']))
    frame=review.cq.horizon.attach_selected(frame,qconfig,metadata,salt,features,{})
    del salt
    boot=stats.Bootstrap(frame.person_key.to_numpy(),500,spec['seed'])
    output={'reporting_mode':'presentation','authorization':spec['authorization'],'employee_level_rows_persisted':False,
            'reason':'Completar captura/error por estado QVoice en 10/20/30 y observado publicable de fichas; no se puede reconstruir de los resúmenes principales.',
            'additional_model_fits':0,'source_query':source['base_query'],'source_query_sha256':review.sha(ROOT/source['base_query']),
            'executed_at':datetime.now(timezone.utc).isoformat(),'qvoice_by_capacity':[],'segments_qvoice_coverage':[],
            'cards_observed':{},'group_rank_stability':{},'checks':[]}
    for period in source['periods']:
        test=review.bu.test_frame(frame,period,loader['knowledge_boundary'])
        ix=test.index.to_numpy();test=test.reset_index(drop=True);y=test.y_6m.to_numpy(float)
        coarse=review.cq.groups.cut_keys(test,[]);parent=coarse[['antiguedad','salidas_equipo','nivel']].agg(' · '.join,axis=1).to_numpy()
        block=next(b for b in results['periods'] if b['period']['id']==period['id'])
        assert block['observations']==len(test) and block['event_exposures']==int(y.sum())
        for name in review.NAMES:
            review.log('Suplemento '+period['id']+' '+name)
            model,q=review.restore(models[period['id'],name])
            p=review.bu.risk_with_correction(model,test,review.bu.q_correction(q,test));rh=model.risk(test)
            state,valid,_=review.qstates(test,models[period['id'],name]['selected']['features'])
            check=abs(np.mean(stats.loss_arrays(y,p)['log_loss'])-block['models'][name]['capacities']['30']['metrics']['log_loss'])
            assert check<1e-10
            output['checks'].append({'period':period['id'],'model':name,'log_loss_reproduction_difference':float(check)})
            for cap in [0.1,0.2,0.3]:
                s=review.structure(test,p,parent,cap);base_s=review.structure(test,rh,parent,cap)
                masks=[state==status for status in ['completa','parcial','ausente']]
                safe=all(test.person_key.iloc[np.flatnonzero(mask&(y==1))].nunique()>=30 for mask in masks)
                for status,mask in zip(['completa','parcial','ausente'],masks):
                    r={'period':period['id'],'model':name,'capacity':int(cap*100),'state':status,
                       'coverage_denominator_person_months':len(test),'person_months':int(mask.sum()),
                       'coverage_percent':float(100*mask.mean()),'observed_publishable':safe}
                    if safe:
                        j=np.flatnonzero(mask)
                        boot.metric_cache.clear()
                        metrics,reps=stats.metrics(y[j],p[j],s['weights'][j],s['cells'][j],boot,ix[j])
                        boot.metric_cache.clear()
                        base_metrics,base_reps=stats.metrics(y[j],rh[j],base_s['weights'][j],boot=boot,cells=base_s['cells'][j],indices=ix[j])
                        # Cada asignación usa capacidad global; cobertura dentro del estado puede diferir.
                        r.update(metrics=metrics,ci95={k:stats.interval(v) for k,v in reps.items()},
                                 RH_same_cohort=base_metrics,
                                 Q_minus_RH={k:{'difference':metrics[k]-base_metrics[k],'ci95':stats.interval(reps[k]-base_reps[k])}
                                             for k in reps if k in base_reps})
                    else:r['reason']='Supresión complementaria: algún estado no reúne 30 personas con evento.'
                    output['qvoice_by_capacity'].append(r)
            for dim,values in [('region',test.region.astype(str).to_numpy()),('level',test.level_grouped.astype(str).to_numpy()),
                              ('tenure',test.tenure_playbook_band.astype(str).to_numpy())]:
                for value in np.unique(values):
                    mask=values==value;counts=[int(np.sum(mask&(state==st))) for st in ['completa','parcial','ausente']]
                    n=int(mask.sum())
                    if test.person_key.iloc[np.flatnonzero(mask)].nunique()<30:continue
                    support=[test.person_key.iloc[np.flatnonzero(mask&(state==st))].nunique() for st in ['completa','parcial','ausente']]
                    okay=all(v==0 or v>=30 for v in support)
                    output['segments_qvoice_coverage'].append({'period':period['id'],'model':name,'dimension':dim,'segment':str(value),
                       'denominator_person_months':n,'complete_partial_absent_percent':[100*v/n for v in counts] if okay else None,
                       'coverage_definition':'Información válida requerida / personas de la foto; agregada por exposiciones en el periodo'})
            primary=review.structure(test,p,parent,.3)
            labels=test.snapshot_date.astype(str)+' | '+primary['labels'];cards=[]
            # Una sola partición disjunta por mes; >=2 celdas ocultas por mes cuando hay alguna.
            for date in sorted(test.snapshot_date.unique()):
                date_mask=test.snapshot_date.to_numpy()==date
                cells=np.unique(labels[date_mask]);counts={}
                for cell in cells:
                    mask=labels.to_numpy()==cell
                    counts[cell]=(int(mask.sum()),int(y[mask].sum()))
                hidden={cell for cell,(n,e) in counts.items() if n<30 or e<30}
                if len(hidden)==1:
                    candidates=[cell for cell in cells if cell not in hidden]
                    if candidates:hidden.add(min(candidates,key=lambda k:counts[k][1]))
                for cell in cells:
                    if cell in hidden:continue
                    mask=labels.to_numpy()==cell;j=np.flatnonzero(mask)
                    row={'cell':str(cell),'observed_publishable':True,'event_exposures':int(y[j].sum()),
                         'distinct_people_with_event':int(test.person_key.iloc[j[y[j]==1]].nunique()),
                         'observed_percent':float(100*y[j].mean()),'absolute_error_pp':float(100*abs((p[j]-y[j]).mean())),
                         'bias_pp':float(100*(p[j]-y[j]).mean()),
                         'observed_rate_ci95_cluster_percent':stats.interval(100*boot.ratio(ix[j],y[j],np.ones(len(j)))),
                         'bias_ci95_cluster_pp':stats.interval(100*boot.ratio(ix[j],p[j]-y[j],np.ones(len(j))))}
                    e=event_map.get(str(cell))
                    if e is not None:
                        assert e['people']==len(j) and e['event_exposures']==int(y[j].sum())
                        row['unique_exit_events']=int(e['unique_exit_events'])
                    cards.append(row)
            output['cards_observed'][period['id']+'/'+name]=cards
            monthly=[]
            for date in sorted(test.snapshot_date.unique()):
                mask=test.snapshot_date.to_numpy()==date
                group=pd.DataFrame({'parent':parent[mask],'p':p[mask]}).groupby('parent').p.agg(['mean','size'])
                monthly.append((date,group.loc[group['size']>=300]))
            transitions=[]
            for (d1,a),(d2,b) in zip(monthly,monthly[1:]):
                common=a.index.intersection(b.index)
                corr=a.loc[common,'mean'].rank().corr(b.loc[common,'mean'].rank()) if len(common)>1 else None
                transitions.append({'from':str(pd.Timestamp(d1).date()),'to':str(pd.Timestamp(d2).date()),'common_groups':len(common),
                    'rank_correlation':float(corr) if corr is not None and np.isfinite(corr) else None,
                    'mean_group_absolute_risk_change_pp':float(100*np.abs(a.loc[common,'mean']-b.loc[common,'mean']).mean())})
            output['group_rank_stability'][period['id']+'/'+name]=transitions
    output['elapsed_seconds']=time.perf_counter()-started
    review.write(out/'cohort-diagnostics-supplement.json',output)
    review.log('Suplemento terminado: sólo agregados; cero reajustes.')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=ROOT/'config/julia_rh_review_20261012.json')
    args=parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    with threadpool_limits(limits=1):main(args.config)
