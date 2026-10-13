"""Revisión CQ/FQ/FQ+BU: una carga en RAM, modelos y agregados reproducibles."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

import numpy as np
import pandas as pd
from scipy import sparse
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import b_incremental_data as data
import engineering_model_c as c
import engineering_model_c_fast as fast
import engineering_model_c_qvoice as cq
import engineering_bu_l3_experiment as bu
import julia_review_statistics as stats

read=bu.read
write=bu.write
sha=bu.sha
NAMES=['CQ','FQ','FQ_BU_L3']


def log(text):
    print(datetime.now(timezone.utc).isoformat(timespec='seconds')+' '+text,flush=True)


def prepared(model,frame):
    return model.pool.apply(frame) if isinstance(model,bu.PooledModel) else frame


def export_model(model,q,selected,cutoff,base_cutoff,source):
    return {'base':(model.model if isinstance(model,bu.PooledModel) else model).artifact(),
            'pool_keep':model.pool.keep if isinstance(model,bu.PooledModel) else None,
            'q_encoder':asdict(q[0]),'q_beta':np.asarray(q[1]).tolist(),
            'selected':selected,'cutoff':cutoff,'base_cutoff':base_cutoff,'source':source,
            'status':'experimental_retrospective','employee_level_rows_persisted':False}


def restore(artifact):
    model=cq.prior.restore_model(artifact['base'])
    if artifact['pool_keep'] is not None: model=bu.PooledModel(model,bu.BUPool(artifact['pool_keep']))
    q=(cq.qmodel.CategoryEncoder(**artifact['q_encoder']),np.array(artifact['q_beta']))
    return model,q


def covariance(model,q,base_frame,qframe,base_cutoff,qcutoff,selected):
    bt=c.train_before(base_frame,base_cutoff)
    qt=c.train_before(qframe,qcutoff)
    xb=model.design.matrix(prepared(model,bt))
    xq=model.design.matrix(prepared(model,qt))
    zq=cq.horizon.category_matrix(q[0],qt)
    cov,detail=stats.sandwich(xb,bt.y_next.to_numpy(float),model.beta,bt.person_key.to_numpy(),
        xq,zq,qt.y_next.to_numpy(float),q[1],qt.person_key.to_numpy(),model.l2*8,selected['l2'])
    detail.update(base_last_label=str(bt.label_end.max().date()),q_last_label=str(qt.label_end.max().date()))
    assert bt.label_end.max()<=pd.Timestamp(base_cutoff) and qt.label_end.max()<=pd.Timestamp(qcutoff)
    return cov,detail


def predict_gradient(model,q,test):
    x=model.design.matrix(prepared(model,test));z=cq.horizon.category_matrix(q[0],test)
    p,g=stats.risk_gradient(x,z,model.beta,q[1],model.design.columns,test.snapshot_date.dt.month.to_numpy())
    check=bu.risk_with_correction(model,test,bu.q_correction(q,test))
    if not np.allclose(p,check,atol=1e-12,rtol=0): raise RuntimeError('No reconcilia el riesgo del gradiente.')
    return p,g


def tables(test,p,gradient,cov,boot,global_indices,keys,weights=None):
    """Tabla con supresión complementaria de todo el bloque observado si hay celdas sin soporte."""
    codes,labels=pd.factorize(keys,sort=True);nc=len(labels)
    sizes=np.bincount(codes,minlength=nc)
    y=test.y_6m.to_numpy(float)
    sums=np.bincount(codes,weights=y,minlength=nc)
    expected=np.bincount(codes,weights=p,minlength=nc)
    unique=np.array([test.person_key.iloc[np.flatnonzero(codes==i)].nunique() for i in range(nc)])
    events=np.array([test.person_key.iloc[np.flatnonzero((codes==i)&(y==1))].nunique() for i in range(nc)])
    valid=(unique>=30)&(events>=30)
    # No publicar otras tasas/errores de esta partición si permitirían restar una celda pequeña.
    observed_block_safe=bool(valid.all())
    den=boot.sums(global_indices,codes,np.ones(len(test)),nc)
    obs=boot.sums(global_indices,codes,y,nc)
    pred=boot.sums(global_indices,codes,p,nc)
    aggregator=sparse.csr_matrix((np.ones(len(test)),(codes,np.arange(len(test)))),shape=(nc,len(test)))
    gmean=(aggregator@gradient)/sizes[:,None]
    se=np.sqrt(np.maximum(np.einsum('ij,jk,ik->i',gmean,cov,gmean),0))
    means=expected/sizes
    selected=np.bincount(codes,weights=weights,minlength=nc) if weights is not None else None
    result=[]
    for i,label in enumerate(labels):
        if unique[i]<30:
            result.append({'cell':'celda_suprimida','suppressed':True,'reason':'Menos de 30 personas distintas'})
            continue
        row={'cell':str(label),'person_month_observations':int(sizes[i]),'distinct_people':int(unique[i]),
             'snapshot_count':int(test.snapshot_date.iloc[np.flatnonzero(codes==i)].nunique()),
             'predicted_risk_percent':float(100*means[i]),
             'estimated_mean_risk_ci95_delta_percent':(100*np.clip([means[i]-1.96*se[i],means[i]+1.96*se[i]],0,1)).tolist(),
             'observed_publishable':observed_block_safe,
             'survey_date':'Desconocida: año de wave conocido; no se acredita fecha individual ni cierre exacto',
             'accredited_availability_date':'No acreditada; regla anual Y → Y+1',
             'rh_first_snapshot':str(test.snapshot_date.iloc[np.flatnonzero(codes==i)].min().date()),
             'rh_last_snapshot':str(test.snapshot_date.iloc[np.flatnonzero(codes==i)].max().date())}
        if selected is not None:
            row['selected_effective_person_months']=float(selected[i])
            row['priority_share_percent']=float(100*selected[i]/weights.sum())
            row['population_share_percent']=float(100*sizes[i]/len(test))
        if observed_block_safe:
            row.update(event_exposures=int(sums[i]),distinct_people_with_event=int(events[i]),
                       observed_percent=float(100*sums[i]/sizes[i]),
                       observed_rate_ci95_cluster_percent=stats.interval(100*obs[:,i]/den[:,i]),
                       bias_pp=float(100*(means[i]-sums[i]/sizes[i])),
                       bias_ci95_cluster_pp=stats.interval(100*(pred[:,i]-obs[:,i])/den[:,i]),
                       absolute_error_pp=float(100*abs(means[i]-sums[i]/sizes[i])))
        else:
            row['observed_suppression_reason']='Bloque observado suprimido: alguna celda tiene menos de 30 personas/eventos distintos; incluye supresión complementaria de tasas, conteos, errores e intervalos.'
        result.append(row)
    return result


def structure(test,p,parent,capacity,minimum=None):
    weights=np.zeros(len(test));low=weights.copy();high=weights.copy()
    label=np.empty(len(test),object);kind=np.empty(len(test),object)
    month_details=[]
    for date in sorted(test.snapshot_date.unique()):
        ix=np.flatnonzero(test.snapshot_date.to_numpy()==date)
        result=stats.partition(parent[ix],test.bu_l3.astype(str).to_numpy()[ix],p[ix],capacity,minimum)
        weights[ix]=result['weights'];low[ix]=result['low'];high[ix]=result['high']
        label[ix]=np.array(result['labels'],object)[result['codes']];kind[ix]=result['kinds']
        selected_sizes=result['n'][result['group_weights']>0]
        rows={'snapshot':str(pd.Timestamp(date).date()),'people':len(ix),
              'effective_people_selected':float(weights[ix].sum()),'whole_groups_excluding_people':int(low[ix].sum()),
              'whole_groups_including_people':int(high[ix].sum()),'priority_groups':len(selected_sizes),
              'priority_median_group_people':float(np.median(selected_sizes)),
              'priority_maximum_group_people':int(selected_sizes.max()),
              'categories':{k:int(np.sum(result['kinds']==k)) for k in ['REST','no_priorizado','padre_conservado','remanente','hijo_BU']},
              'bu_categories_in_priority':int(test.bu_l3.iloc[ix[weights[ix]>0]].nunique()),
              'identifiable_bu_priority_percent':float(100*np.sum(weights[ix]*(result['kinds']=='hijo_BU'))/weights[ix].sum())}
        assert sum(rows['categories'].values())==len(ix)
        month_details.append(rows)
    cells,_=pd.factorize(test.snapshot_date.astype(str)+' | '+pd.Series(label,index=test.index),sort=True)
    return {'weights':weights,'low':low,'high':high,'labels':label,'kinds':kind,'cells':cells,'monthly':month_details}


def qstates(test,features):
    values=np.column_stack([test[f].astype(str).to_numpy() for f in features])
    valid=np.isin(values,cq.VALID)
    status=np.where(valid.all(axis=1),'completa',np.where(valid.any(axis=1),'parcial','ausente'))
    states={}
    for state in ['missing','no_linked_row','different_employment_episode','no_available_wave','question_absent']:
        states[state]=int(np.sum(np.any(values==state,axis=1)))
    # El total de estados no es aditivo: una persona puede tener varios campos ausentes.
    return status,valid,states


def checkpoint(out,state,started,**kwargs):
    write(out/'manifest.json',{'status':state,'updated_at':datetime.now(timezone.utc).isoformat(),
        'reporting_mode':'presentation','authorization':'config/attrition_model_in_memory_training_authorization_20261001.json',
        'employee_level_rows_persisted':False,'individual_scores_published':False,
        'elapsed_seconds':time.perf_counter()-started,**kwargs})


def calibration_check(base_frame,qframe,period,model_name,model,selected,y,p,metric,reps,spec,cconfig,out):
    ci=stats.interval(reps['bias_pp'])
    triggered=abs(metric['bias_pp'])>=spec['calibration_bias_trigger_pp'] and ci[0]*ci[1]>0
    result={'triggered':triggered,'bias_pp':metric['bias_pp'],'bias_ci95_pp':ci,
            'status':'identity_no_trigger','multiplier':1.,'recommended':False,'origins':[]}
    if not triggered: return result
    possible=[]
    for d in sorted(qframe.snapshot_date.unique()):
        d=pd.Timestamp(d)
        if d+pd.DateOffset(months=6)>pd.Timestamp(period['origin']): continue
        tr=c.train_before(qframe,d)
        if tr.snapshot_date.nunique()>=1 and tr.y_next.sum()>=30:
            possible.append(d)
    possible=possible[-3:]
    result['eligible_origins']=[str(d.date()) for d in possible]
    if len(possible)<3:
        result['status']='identity_insufficient_history';return result
    ys=[];ps=[]
    for d in possible:
        log(f'Calibración auxiliar {period["id"]} {model_name} {d.date()}')
        tr=c.train_before(base_frame,d)
        pool=bu.BUPool.fit(tr,300) if model_name=='FQ_BU_L3' else None
        prepared_train=pool.apply(tr) if pool else tr
        design=c.Design.fit(prepared_train,list(model.features),cconfig['interactions'])
        aux=fast.fit_context(design,design.matrix(prepared_train),tr.y_next.to_numpy(float),list(model.features),model.l2,cconfig)
        if pool: aux=bu.PooledModel(aux,pool)
        q=bu.fit_q(aux,qframe,str(d.date()),selected)
        test=qframe.loc[(qframe.snapshot_date==d)&qframe.y_6m.notna()]
        prediction=bu.risk_with_correction(aux,test,bu.q_correction(q,test))
        ys.append(test.y_6m.to_numpy(float));ps.append(prediction)
        provenance={'origin':str(d.date()),'base_last_label':str(tr.label_end.max().date()),
                    'q_last_label':str(c.train_before(qframe,d).label_end.max().date()),
                    'outcome_end':str((d+pd.DateOffset(months=6)).date())}
        result['origins'].append(provenance)
        write(out/'models'/f'aux-{period["id"]}-{model_name}-{d.date()}.json',
              export_model(aux,q,selected,str(d.date()),str(d.date()),'Ajuste auxiliar sólo con etiquetas anteriores al origen'))
        del tr,prepared_train,aux,q,test
        gc.collect()
    scalar=cq.horizon.fit_scalar(np.concatenate(ys),np.concatenate(ps),[-1.5,1.5])
    corrected=cq.horizon.transform_risk(p,scalar['log_multiplier'])
    old=stats.loss_arrays(y,p);new=stats.loss_arrays(y,corrected)
    improvement=abs((corrected-y).mean())<abs((p-y).mean())
    guards=improvement and all(new[k].mean()<=old[k].mean() for k in old)
    result.update(status='scalar_tested',scalar=scalar,multiplier=scalar['multiplier'],recommended=bool(guards),
                  posterior_bias_pp=float(100*(corrected-y).mean()),
                  posterior_log_loss=float(new['log_loss'].mean()),posterior_brier=float(new['brier'].mean()),
                  limitation='Diagnóstico retrospectivo activado por el test; variables y penalizaciones congeladas. Auxiliares ajustados sólo con etiquetas anteriores a su origen. No es validación prospectiva ni nueva selección anidada.')
    return result


def run(config_path,resume_models=False):
    started=time.perf_counter();spec=read(config_path);out=ROOT/spec['output']
    if (out/'results.json').exists(): raise RuntimeError('La corrida finalizada se conserva; use otra carpeta.')
    out.mkdir(parents=True,exist_ok=True)
    base_spec=read(ROOT/spec['source_config']);cconfig=read(ROOT/base_spec['c_config']);cqconfig=read(ROOT/base_spec['cq_config'])
    assert (out/'documentacion/matriz-comentarios.json').exists()
    checkpoint(out,'running_preflight',started,run_id=spec['run_id'])
    write(out/'frozen-config.json',spec)
    source_files=[config_path,ROOT/spec['source_config'],ROOT/'tools/engineering_julia_rh_review.py',ROOT/'tools/julia_review_statistics.py',
                  ROOT/base_spec['base_query'],ROOT/base_spec['source_c_config'],ROOT/base_spec['loader_config'],ROOT/base_spec['cq_config'],ROOT/base_spec['c_config']]
    source_files += [ROOT/cqconfig['output']/'folds'/p['id']/'model.json' for p in base_spec['periods']]
    source_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in source_files}
    for p in source_files:
        dst=out/'source'/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    bu.copy_evidence(base_spec,out)
    log('Validación agregada del mapping BU L3: población, as-of y unicidad.')
    # Definición previa: mapping as-of por foto; cero multi-match/duplicados, sin reemplazo por mapping futuro.
    audit=bu.audit_bu_l3(base_spec,out)
    unique_events=bu.run_aggregate_query(ROOT/'queries/audits/julia_review_unique_events_20261012.sql',out,'unique-events',100)
    loader=bu.loader_config(base_spec,out)
    log('Una carga compartida: RH y QVoice sólo en RAM.')
    frame,qframe=data.load(loader,out)
    # Se conserva la misma secuencia de personas y resultados para todos los estimadores.
    periods=base_spec['periods']
    alltest=pd.concat([bu.test_frame(qframe,p,loader['knowledge_boundary']) for p in periods],ignore_index=True)
    if alltest.duplicated(['person_key','snapshot_date']).any(): raise RuntimeError('Duplicados en evaluación.')
    boot=stats.Bootstrap(alltest.person_key.to_numpy(),spec['bootstrap_repetitions'],spec['seed'])
    period_results=[];held=[];encodings=[];fits={'base':0,'q':0};offset=0
    for period in periods:
        log('Periodo '+period['id'])
        archival=read(ROOT/cqconfig['output']/'folds'/period['id']/'model.json')
        base=cq.prior.restore_model(archival['base_model'])
        selected=archival['selected']
        q=(cq.qmodel.CategoryEncoder(**archival['correction']['encoder']),np.array(archival['correction']['beta']))
        test=bu.test_frame(qframe,period,loader['knowledge_boundary']).reset_index(drop=True)
        global_ix=np.arange(offset,offset+len(test));offset+=len(test)
        y=test.y_6m.to_numpy(float)
        keys=cq.groups.cut_keys(test,[])
        parent=keys[cqconfig['groups']].agg(' · '.join,axis=1).to_numpy()
        # Cinco bandas comunes fijadas en la distribución CQ de la última foto anterior al periodo.
        history=qframe.loc[qframe.snapshot_date<pd.Timestamp(period['origin'])]
        history=history.loc[history.snapshot_date==history.snapshot_date.max()]
        prior_pred=bu.risk_with_correction(base,history,bu.q_correction(q,history))
        limits=np.quantile(prior_pred,[.2,.4,.6,.8])
        write(out/'bands'/f'{period["id"]}.json',{'limits':limits,'source_snapshot':str(history.snapshot_date.max().date()),
               'method':'Cuantiles CQ en última foto previa; límites comunes a los tres modelos, sin outcomes del test'})
        block={'period':period,'people':int(test.person_key.nunique()),'observations':len(test),
               'event_exposures':int(y.sum()),'distinct_people_with_event':int(test.loc[test.y_6m==1,'person_key'].nunique()),
               'models':{},'source_query':base_spec['base_query'],'query_date':datetime.now(timezone.utc).date().isoformat()}
        event_check=next(r for r in unique_events['rows'] if r['period']==period['id'])
        if int(event_check['event_exposures'])!=block['event_exposures'] or int(event_check['distinct_people_with_event'])!=block['distinct_people_with_event']:
            raise RuntimeError('No reconcilia el conteo independiente de eventos.')
        block['unique_exit_events']=int(event_check['unique_exit_events'])
        block['one_exit_per_event_person']=block['unique_exit_events']==block['distinct_people_with_event']
        internal={'period':period,'test':test,'predictions':{},'scenarios':{},'replicates':{}}
        for name in NAMES:
            log('Estimador '+name+' '+period['id'])
            file=out/'models'/f'{period["id"]}-{name}.json'
            if name=='CQ':
                model=base;fitted=q;base_cutoff=archival['base_model_origin']
            elif resume_models and file.exists():
                model,fitted=restore(read(file));base_cutoff=period['origin']
            else:
                additions=['work_city']+(['bu_l3'] if name=='FQ_BU_L3' else [])
                model=bu.fit_c_addition(frame,period['origin'],base,additions,cconfig)
                fitted=bu.fit_q(model,qframe,period['origin'],selected)
                base_cutoff=period['origin'];fits['base']+=1;fits['q']+=1
            if 'job_family_detail' in model.features: raise RuntimeError('Predictor excluido.')
            artifact=export_model(model,fitted,selected,period['origin'],base_cutoff,archival['base_model_reference'] if name=='CQ' else 'Ajuste RH con composición y L2 congelados')
            write(file,artifact)
            restored,rq=restore(artifact)
            p,gradient=predict_gradient(model,fitted,test)
            if not np.allclose(p,bu.risk_with_correction(restored,test,bu.q_correction(rq,test)),atol=1e-12,rtol=0):
                raise RuntimeError('No reproduce modelo guardado.')
            cov,detail=covariance(model,fitted,frame,qframe,base_cutoff,period['origin'],selected)
            write(out/'models'/f'{period["id"]}-{name}-covariance.json',{'covariance':cov,'detail':detail})
            for component,encoder in [('RH',artifact['base']['encoder']),('QVoice',artifact['q_encoder'])]:
                for f in encoder['features']:
                    encodings.append({'period':period['id'],'model':name,'component':component,'feature':f,
                                      'levels':encoder['levels'][f],'reference':encoder['references'][f],
                                      'pool_keep':artifact['pool_keep'] if f=='bu_l3' else None})
            state,valid,absence=qstates(test,selected['features'])
            band=np.array(['B'+str(i+1) for i in np.searchsorted(limits,p,side='right')])
            model_result={'selected':selected,'base_features':model.features,'covariance':detail,'capacities':{},'subdivision':{},
                          'qvoice_absence_states_nonadditive':{k:(v if v>=30 else None) for k,v in absence.items()},
                          'qvoice_denominator':'Todas las personas de la foto; no es tasa de participación entre invitados',
                          'unknown_categories':{},'calibration':{}}
            model_result['global_ranking']=c.metrics(test,p)
            for f in fitted[0].features:
                unknown=~test[f].astype(str).isin(fitted[0].levels[f])
                model_result['unknown_categories'][f]={'has_unseen':bool(unknown.any()),'count':int(unknown.sum()) if unknown.sum()>=30 else None,
                   'behavior':'Término con indicadores cero; persisten intercepto y demás términos de la corrección'}
            internal['predictions'][name]=p;internal['scenarios'][name]={};internal['replicates'][name]={}
            for fraction in spec['capacities']:
                cap=str(int(fraction*100))
                s=structure(test,p,parent,fraction)
                met,rep=stats.metrics(y,p,s['weights'],s['cells'],boot,global_ix)
                model_result['capacities'][cap]={'metrics':met,'ci95':{k:stats.interval(v) for k,v in rep.items()},'monthly':s['monthly']}
                for boundary in ['low','high']:
                    boundary_met,_=stats.metrics(y,p,s[boundary],s['cells'],boot,global_ix)
                    model_result['capacities'][cap][boundary]=boundary_met
                internal['scenarios'][name][cap]=s;internal['replicates'][name][cap]=rep
                for minimum in spec['child_minima']:
                    sub=structure(test,p,parent,fraction,minimum)
                    sm,sr=stats.metrics(y,p,sub['weights'],sub['cells'],boot,global_ix)
                    med=np.mean([r['priority_median_group_people'] for r in sub['monthly']])
                    base_med=np.mean([r['priority_median_group_people'] for r in s['monthly']])
                    guard={'median_smaller':bool(med<base_med),'capture_loss_within_2pct':bool(sm['capture_percent']>=met['capture_percent']*.98),
                           'error_increase_within_0_1pp':bool(sm['group_snapshot_mae_pp']<=met['group_snapshot_mae_pp']+.1),
                           'capacity_preserved':bool(abs(sm['coverage_percent']-fraction*100)<1e-8),
                           'true_rest_not_increased':all(a['categories']['REST']==b['categories']['REST'] for a,b in zip(s['monthly'],sub['monthly']))}
                    model_result['subdivision'][cap+'/'+str(minimum)]={'metrics':sm,'monthly':sub['monthly'],'guards':guard,
                       'passes':all(guard.values()),'delta_ci95':{k:stats.interval(sr[k]-rep[k]) for k in ['capture_percent','group_snapshot_mae_pp']}}
                    internal['scenarios'][name][cap+'/'+str(minimum)]=sub
            primary=internal['scenarios'][name]['30']
            model_result['diagnostics']={}
            for dim,values in [('period',np.repeat(period['id'],len(test))),('month',test.snapshot_date.astype(str).to_numpy()),
                               ('risk_band',band),('region',test.region.astype(str).to_numpy()),
                               ('level',test.level_grouped.astype(str).to_numpy()),('tenure',test.tenure_playbook_band.astype(str).to_numpy()),('qvoice',state)]:
                model_result['diagnostics'][dim]=tables(test,p,gradient,cov,boot,global_ix,values,primary['weights'])
            # Riesgo por mes/banda y grupo; la supresión se aplica por partición completa.
            model_result['diagnostics']['month_band']=tables(test,p,gradient,cov,boot,global_ix,test.snapshot_date.astype(str)+' | '+band)
            model_result['diagnostics']['group_window']=tables(test,p,gradient,cov,boot,global_ix,primary['labels'],primary['weights'])
            model_result['group_cards']=tables(test,p,gradient,cov,boot,global_ix,test.snapshot_date.astype(str)+' | '+primary['labels'],primary['weights'])
            for row in model_result['group_cards']:
                if row.get('suppressed'):continue
                row.update(topic_to_validate='Continuidad, desarrollo y capacidad del equipo; contrastar con escucha agregada',
                           owner_function='RH de la población; liderazgo operativo',candidate_action='Revisión de vacantes, soporte y oportunidades de desarrollo',
                           followup_indicator='Acuerdos con responsable y fecha; revisión de cobertura y error de la siguiente cohorte madura',
                           suggested_deadline='30 días para contraste; 90 días para seguimiento',
                           survey_wave='2024' if period['id']=='aug_dec_2025' else '2025',
                           operational_survey_age='No acreditada; fecha de encuesta/publicación desconocida')
                mask=(test.snapshot_date.astype(str)+' | '+primary['labels']).to_numpy()==row['cell']
                qcounts=[int(np.sum(state[mask]==s)) for s in ['completa','parcial','ausente']]
                qsafe=all(v==0 or v>=30 for v in qcounts)
                for field,value in zip(['qvoice_complete_percent','qvoice_partial_percent','qvoice_absent_percent'],qcounts):
                    row[field]=100*value/int(mask.sum()) if qsafe else None
                row['qvoice_coverage_denominator']=int(mask.sum())
                row['qvoice_block_coverage_percent']={f:(float(100*valid[mask,i].mean()) if
                    all(v==0 or v>=30 for v in [int(valid[mask,i].sum()),int(mask.sum()-valid[mask,i].sum())]) else None)
                    for i,f in enumerate(selected['features'])}
                row['unique_exit_events']=row.get('distinct_people_with_event') if block['one_exit_per_event_person'] else None
            rh=model.risk(test)
            model_result['qvoice_vs_RH_same_cohorts']=[]
            for status in ['completa','parcial','ausente']:
                ix=np.flatnonzero(state==status)
                if len(ix)<30 or test.person_key.iloc[ix[y[ix]==1]].nunique()<30:
                    model_result['qvoice_vs_RH_same_cohorts'].append({'state':status,'suppressed':True});continue
                r={'state':status,'people':int(test.person_key.iloc[ix].nunique()),
                   'mean_Q_minus_RH_risk_pp':float(100*np.mean(p[ix]-rh[ix])),
                   'maximum_absolute_Q_minus_RH_pp':float(100*np.max(np.abs(p[ix]-rh[ix]))),
                   'equals_RH':bool(np.allclose(p[ix],rh[ix],atol=1e-12))}
                # Se publican diferencias pareadas de pérdidas, no conteos de eventos de una celda suprimida.
                for metric,a in stats.loss_arrays(y[ix],p[ix]).items():
                    delta=a-stats.loss_arrays(y[ix],rh[ix])[metric]
                    r[metric+'_delta']=float(delta.mean())
                    r[metric+'_delta_ci95']=stats.interval(boot.ratio(global_ix[ix],delta,np.ones(len(ix))))
                model_result['qvoice_vs_RH_same_cohorts'].append(r)
            # Mismo conjunto priorizado por CQ: atribuir diferencias al estimador.
            common=internal['scenarios']['CQ']['30']
            model_result['on_common_CQ_priority'],_=stats.metrics(y,p,common['weights'],common['cells'],boot,global_ix)
            model_result['calibration']=calibration_check(frame,qframe,period,name,model,selected,y,p,
                model_result['capacities']['30']['metrics'],internal['replicates'][name]['30'],spec,cconfig,out)
            block['models'][name]=model_result
            write(out/'periods'/f'{period["id"]}-{name}.json',model_result)
            checkpoint(out,'running_diagnostics',started,run_id=spec['run_id'],last_completed=period['id']+'/'+name,primary_fits=fits)
            del gradient,cov,restored,rq,model,fitted
            gc.collect()
        period_results.append(block);held.append(internal)
        write(out/'periods'/f'{period["id"]}.json',block)
    assert fits['base']<=4 and fits['q']<=4
    summary={};differences={};stability={};subdivision=[]
    for name in NAMES:
        summary[name]={}
        for cap in ['10','20','30']:
            mets=[b['models'][name]['capacities'][cap]['metrics'] for b in period_results]
            summary[name][cap]={k:float(np.mean([m[k] for m in mets])) for k in mets[0]}
            summary[name][cap]['ci95']={k:stats.interval(np.mean([h['replicates'][name][cap][k] for h in held],axis=0)) for k in held[0]['replicates'][name][cap]}
        p=np.concatenate([h['predictions'][name] for h in held])
        stability[name]={}
        for scenario in held[0]['scenarios'][name]:
            w=np.concatenate([h['scenarios'][name][scenario]['weights'] for h in held])
            labels=np.concatenate([h['scenarios'][name][scenario]['labels'] for h in held])
            stability[name][scenario]=stats.stability(alltest,p,w,labels)
        for cap in ['10','20','30']:
            for minimum in spec['child_minima']:
                scenarios=[b['models'][name]['subdivision'][cap+'/'+str(minimum)] for b in period_results]
                subdivision.append({'model':name,'capacity':int(cap),'minimum':minimum,
                    'passes_both_periods':all(s['passes'] for s in scenarios),
                    'capture_percent':float(np.mean([s['metrics']['capture_percent'] for s in scenarios])),
                    'error_pp':float(np.mean([s['metrics']['group_snapshot_mae_pp'] for s in scenarios])),
                    'median_people':float(np.mean([np.mean([r['priority_median_group_people'] for r in s['monthly']]) for s in scenarios])),
                    'period_guards':[s['guards'] for s in scenarios]})
    for a,b in [('FQ','CQ'),('FQ_BU_L3','CQ'),('FQ_BU_L3','FQ')]:
        differences[a+'_minus_'+b]={}
        for cap in ['10','20','30']:
            differences[a+'_minus_'+b][cap]={k:{'difference':summary[a][cap][k]-summary[b][cap][k],
                'ci95':stats.interval(np.mean([h['replicates'][a][cap][k]-h['replicates'][b][cap][k] for h in held],axis=0))}
                for k in held[0]['replicates'][a][cap]}
    reproduction=[]
    for block in period_results:
        historical=read(ROOT/cqconfig['output']/'folds'/block['period']['id']/'evaluation.json')
        # Esquema histórico inspeccionado: dict de modelos con global/scenarios.
        h=historical['CQ'] if 'CQ' in historical else historical.get('evaluation',{}).get('CQ')
        if h is None: raise RuntimeError('No se reconoce la evaluación CQ archivada.')
        m=block['models']['CQ']['capacities']['30']['metrics']
        for key,old in [('log_loss',h['global']['log_loss']),('brier',h['global']['brier_score']),
                        ('capture_percent',h['scenarios']['30']['metrics']['capture_percent']),
                        ('group_snapshot_mae_pp',h['scenarios']['30']['metrics']['group_snapshot_mae_pp'])]:
            reproduction.append({'period':block['period']['id'],'metric':key,'archived':old,'current':m[key],
                                 'difference':m[key]-old,'within_1e_8':bool(abs(m[key]-old)<=1e-8)})
    result={'run_id':spec['run_id'],'reporting_mode':'presentation','periods':period_results,'summary':summary,
        'paired_differences':differences,'subdivision':subdivision,'monthly_stability':stability,'reproduction':reproduction,
        'primary_fits':fits,'source_hashes':source_hashes,'knowledge_limitations':spec['knowledge_limitations'],
        'bootstrap':{'repetitions':500,'cluster':'persona','shared_across_periods_and_models':True,'period_weights':[.5,.5],
                     'scope':'Modelos, variables y prioridades fijos; horizontes superpuestos conservados por persona'},
        'authorization':spec['authorization'],'employee_level_rows_persisted':False,'elapsed_seconds':time.perf_counter()-started}
    write(out/'documentacion/codificaciones-modelos.json',{'rows':encodings})
    write(out/'results.json',result)
    write(out/'verification.json',{'same_people_dates_outcomes':True,'no_duplicate_person_snapshot':True,
         'base_and_child_population_conserved':True,'capacities_preserved':True,'model_serialization_reproduced':True,
         'archived_CQ_reproduced':all(x['within_1e_8'] for x in reproduction),'primary_fits':fits,
         'future_training_labels':False,'historical_feature_publication_fully_accredited':False,
         'employee_level_rows_persisted':False,'source_files_unchanged':all(sha(ROOT/p)==h for p,h in source_hashes.items())})
    checkpoint(out,'computed_pending_report_review',started,run_id=spec['run_id'],primary_fits=fits,
               files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'})
    log('Cálculo completo; sólo modelos, parámetros y agregados persistidos.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config',default='config/julia_rh_review_20261012.json');parser.add_argument('--resume-models',action='store_true')
    args=parser.parse_args()
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    with threadpool_limits(limits=1):run(ROOT/args.config,args.resume_models)
