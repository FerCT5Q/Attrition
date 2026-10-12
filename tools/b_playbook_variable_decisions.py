"""Explica selecciones guardadas; no entrena, consulta ni modifica decisiones."""
from __future__ import annotations

from collections import Counter

import engineering_b_incremental as inc
import engineering_model_c as base


def guard_details(trial, baseline, config, mode):
    """Desglosa la misma regla con valores y umbrales, verificando su equivalencia."""
    rows=[]
    def check(name, observed, threshold, passed, unit):
        rows.append({'criterion':name,'observed':observed,'threshold':threshold,
                     'pass':bool(passed),'unit':unit})
    check('Ajuste correcto',trial.get('status'),'ok',trial.get('status')=='ok','estado')
    if trial.get('status')=='ok' or 'eligible_for_selection' in trial:
        check('Elegible para selección',trial.get('eligible_for_selection',True),True,
              trial.get('eligible_for_selection',True),'booleano')
    if trial.get('status')=='ok':
        m,b,s=trial['metrics'],baseline['metrics'],config['selection']
        limit=b['brier_score']*(1+s['maximum_relative_brier_worsening'])
        check('Brier no empeora',m['brier_score'],limit,m['brier_score']<=limit+1e-12,'pérdida media')
        limit=b['pr_auc']*s['minimum_relative_pr_auc']
        check('PR-AUC conserva al menos el 99%',m['pr_auc'],limit,m['pr_auc']>=limit-1e-12,'PR-AUC')
        if mode=='r6':
            limit=b['lift_at_10_percent']*s['minimum_relative_lift10']
            check('Lift al 10% conserva al menos el 99%',m['lift_at_10_percent'],limit,
                  m['lift_at_10_percent']>=limit-1e-12,'razón')
            limit=b['common_group_snapshot_mae_pp']+s['maximum_common_group_mae_worsening_pp']
            check('Error de grupos dentro de tolerancia',m['common_group_snapshot_mae_pp'],limit,
                  m['common_group_snapshot_mae_pp']<=limit+1e-12,'pp')
            limit=b['capture_percent']-s['maximum_capture_loss_pp']
            check('Captura dentro de tolerancia',m['capture_percent'],limit,
                  m['capture_percent']>=limit-1e-12,'%')
    passed=all(r['pass'] for r in rows)
    if passed!=inc.meets_guards(trial,baseline,config,mode):
        raise RuntimeError('La explicación de las guardas no reproduce la selección.')
    return rows


def trial_reason(trial, support, details, family, config):
    if trial.get('status')!='ok':
        return 'Falló el ajuste individual: '+str(trial.get('reason','ninguna penalización produjo un ajuste válido'))+'.'
    problems=[]
    if family=='RH' and not support['eligible_for_selection']:
        if support['observable_training_snapshots']<config['minimum_observable_training_snapshots_for_selection']:
            problems.append(f"Sólo {support['observable_training_snapshots']} fotos observables de entrenamiento; se requieren seis.")
        if support['training_categories']<=1:
            problems.append('Sólo una categoría después de codificar; no hay contraste aprendible.')
    if family=='QVoice' and not trial.get('eligible_for_selection',True):
        if trial.get('availability_control_failed'):
            problems.append('No se pudo ajustar el control de disponibilidad emparejado.')
        elif trial.get('content_improves_availability') is False:
            problems.append('El contenido no reduce log-loss frente al control de su misma disponibilidad.')
        else:
            problems.append('El registro marca la candidata como no elegible.')
    failed=[r['criterion'] for r in details if not r['pass'] and r['criterion'] not in {'Ajuste correcto','Elegible para selección'}]
    if failed:
        problems.append('No supera: '+', '.join(failed)+'.')
    return ' '.join(problems) or 'La incorporación individual cumple las condiciones de validación.'


def describe_selection(selection, path, config, catalog):
    family='RH' if 'candidate_availability' in selection else 'QVoice'
    anchor='B' if family=='RH' else selection['anchor']
    cutoff=selection['cutoff']
    period=next((p['id'] for p in config['periods'] if p['origin']==cutoff),'final')
    if period=='final' and cutoff!=config['knowledge_boundary']:
        raise RuntimeError('Corte de selección desconocido.')
    phase='selección final experimental' if period=='final' else 'selección para evaluación externa'
    mode=selection['split']['selection_mode']
    baseline=selection['baseline']
    winner=selection['winner']
    options=[baseline]+[r for r in selection['trials'] if r.get('stage') in {'single','combination'}]
    replay=inc.choose(options,baseline,config,mode)
    if replay['id']!=winner['id'] or replay.get('l2')!=winner.get('l2'):
        raise RuntimeError('La decisión guardada no coincide con las opciones registradas.')
    viable=[r for r in options if inc.meets_guards(r,baseline,config,mode)]
    best=min(r['metrics']['log_loss'] for r in viable)
    ceiling=best*(1+config['selection']['log_loss_parsimony_relative_tolerance'])+1e-12
    expected=inc.hr_candidates(config) if family=='RH' else inc.q_candidates(config)
    singles={r['additions'][0]:(i,r) for i,r in enumerate(selection['trials']) if r.get('stage')=='single'}
    if set(singles)!=set(expected):
        raise RuntimeError('Falta una prueba individual en '+str(path))
    rows=[]
    for feature in expected:
        index,trial=singles[feature]
        support=selection.get('candidate_availability',{}).get(feature,{})
        details=guard_details(trial,baseline,config,mode)
        passing=all(r['pass'] for r in details)
        individual_reason=trial_reason(trial,support,details,family,config)
        selected=feature in winner['additions']
        combos=[r for r in selection['trials'] if r.get('stage')=='combination' and feature in r['additions']]
        eligible_combos=[r for r in combos if inc.meets_guards(r,baseline,config,mode)]
        shortlisted=feature in selection['shortlist']
        if selected:
            partners=[catalog[f]['label'] for f in winner['additions'] if f!=feature]
            reason='Seleccionada '+('en combinación con '+', '.join(partners) if partners else 'como única incorporación')+'.'
            if not passing:
                reason+=' La combinación sí cumple, aunque la prueba individual no supera todas las condiciones.'
        elif passing or eligible_combos:
            reason=('No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, '
                    'pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima.')
        elif not shortlisted:
            reason='No seleccionada. '+individual_reason+' No entró en las seis primeras para pares y tríos.'
        else:
            reason='No seleccionada. '+individual_reason+' Ninguna combinación probada que la incluye supera todas las condiciones.'
        m=trial.get('metrics',{})
        b=baseline['metrics']
        ac=trial.get('availability_control',{}).get('metrics',{})
        relative=path.relative_to(base.ROOT).as_posix()
        row={
            'feature':feature,'label':catalog[feature]['label'],'family':family,
            'anchor':anchor,'period':period,'phase':phase,'cutoff':cutoff,'selection_mode':mode,
            'selected':selected,'decision':'Seleccionada' if selected else 'No seleccionada',
            'reason':reason,'individual_reason':individual_reason,
            'individual_fit_status':trial['status'],
            'individual_eligible':trial.get('eligible_for_selection',True if trial['status']=='ok' else None),
            'individual_passes_guards':passing,'individual_guard_details':details,
            'individual_failed_guards':[r['criterion'] for r in details if not r['pass']],
            'shortlisted':shortlisted,'combinations_tested':len(combos),
            'combinations_passing_guards':len(eligible_combos),
            'best_admissible_combination':min(eligible_combos,key=lambda r:r['metrics']['log_loss'])['id'] if eligible_combos else None,
            'winner_features':winner['additions'],'winner_id':winner['id'],
            'winner_log_loss':winner['metrics']['log_loss'],
            'best_admissible_log_loss':best,'parsimony_log_loss_ceiling':ceiling,
            'individual_within_parsimony_window':bool(passing and m['log_loss']<=ceiling),
            'training_support':support,'split':selection['split'],
            'individual_l2':trial.get('l2'),'individual_metrics':m,
            'baseline_id':baseline['id'],'baseline_metrics':b,'availability_metrics':ac,
            'content_improves_availability':trial.get('content_improves_availability'),
            'individual_log_loss_gain_relative_percent':100*(b['log_loss']-m['log_loss'])/b['log_loss'] if m else None,
            'individual_brier_gain_relative_percent':100*(b['brier_score']-m['brier_score'])/b['brier_score'] if m else None,
            'individual_capture_gain_pp':m.get('capture_percent',0)-b.get('capture_percent',0) if m and mode=='r6' else None,
            'selection_file':relative,'selection_trial_index_zero_based':index,
            'external_outcomes_used_for_selection':False,
        }
        rows.append(row)
    if family=='RH':
        for feature in config['base_features']:
            rows.append({'feature':feature,'label':catalog[feature]['label'],'family':'B','anchor':'B',
                'period':period,'phase':phase,'cutoff':cutoff,'selection_mode':mode,
                'selected':True,'decision':'Obligatoria en B',
                'reason':'Se conserva por instrucción del usuario; esta ronda no elimina términos de B.',
                'selection_file':path.relative_to(base.ROOT).as_posix(),
                'split':selection['split'],'external_outcomes_used_for_selection':False})
    return rows


def attach_external(decisions, results):
    periods={r['period']['id']:r for r in results['periods']}
    for row in decisions:
        if row['period']=='final' or row['family']=='B':
            continue
        period=periods[row['period']]
        candidate=next(c for c in period['candidates'] if c['feature']==row['feature']
                       and c['family']==row['family'] and c.get('anchor','B')==row['anchor'])
        row['external_fit_status']=candidate['status']
        row['external_reason']=candidate.get('reason')
        row['external_training_support']=candidate.get('training_support',{})
        row['external_metrics']=candidate.get('metrics',{})
        row['external_eligible_history']=candidate.get('training_support',{}).get('eligible_for_selection')
        row['external_availability_metrics']=candidate.get('matched_availability_metrics',{})
        if candidate['status']=='ok':
            m,b=candidate['metrics'],period['metrics'][row['anchor']]
            row['external_log_loss_gain_relative_percent']=100*(b['log_loss']-m['log_loss'])/b['log_loss']
            row['external_brier_gain_relative_percent']=100*(b['brier_score']-m['brier_score'])/b['brier_score']
            row['external_capture_gain_pp']=m['capture_percent']-b['capture_percent']
            row['external_comparable']=bool(row['external_eligible_history']) if row['family']=='RH' else True


def encodings(out, catalog):
    result=[]
    for path in sorted((out/'models').glob('*.json')):
        saved=base.read(path)
        hr=saved.get('base',saved)
        components=[('RH',hr['model']['encoder'],hr.get('rare_pool',{}))]
        if saved.get('correction'):
            components.append(('QVoice',saved['correction']['encoder'],{}))
        for component,encoder,pool in components:
            for feature in encoder['features']:
                if feature not in catalog:
                    raise RuntimeError('Columna de modelo fuera del diccionario: '+feature)
                reference=encoder['references'][feature]
                levels=encoder['levels'][feature]
                columns=[c for c in encoder['columns'] if c.startswith(feature+'=')]
                if reference not in levels or len(columns)!=len(levels)-1:
                    raise RuntimeError('No coinciden referencia y niveles aprendidos.')
                result.append({'model_file':path.relative_to(base.ROOT).as_posix(),
                    'model_name':path.stem,'component':component,'training_cutoff':saved['training_cutoff'],
                    'feature':feature,'label':catalog[feature]['label'],
                    'reference':reference,'learned_levels':levels,'indicator_columns':columns,
                    'indicator_count':len(columns),'rare_pool_keep':pool.get(feature),
                    'rare_pool_applied':feature in pool,
                    'unknown_at_prediction':'(other), si existe pooling; después indicadores cero si el estado no fue aprendido.'
                        if feature in pool else 'Indicadores cero: equivale a la referencia para este término.'})
    return result


def build(out, config, catalog, results):
    decisions=[]
    paths=sorted((out/'selection').glob('*.json'))
    for path in paths:
        decisions+=describe_selection(base.read(path),path,config,catalog)
    attach_external(decisions,results)
    counts=Counter(r['family'] for r in decisions)
    if len(paths)!=12 or counts!={'B':60,'RH':246,'QVoice':306}:
        raise RuntimeError('Cobertura de decisiones incompleta: '+str(counts))
    keys=[(r['feature'],r['anchor'],r['period']) for r in decisions]
    if len(keys)!=len(set(keys)):
        raise RuntimeError('Decisiones duplicadas.')
    return decisions,encodings(out,catalog)
