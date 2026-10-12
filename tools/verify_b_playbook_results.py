"""Valida la ejecución terminada y resume sólo controles/resultados agregados."""
from __future__ import annotations

from collections import Counter
import json
import math

import engineering_b_incremental as inc
import engineering_model_c as base


def require(value, message):
    if not value:
        raise RuntimeError(message)


def main():
    config = base.read(inc.DEFAULT)
    out = base.ROOT/config['output']
    manifest = base.read(out/'manifest.json')
    require(manifest['status']=='completed_experimental','La ejecución no está completa.')
    results = base.read(out/'results.json')
    require(results['mandatory_features']==list(inc.B_TERMS),'Se alteró B.')
    require(not results['external_outcomes_used_for_selection'],'La selección recibió outcomes externos.')
    require(not results['employee_level_rows_persisted'] and not results['individual_scores_published'],
            'El resultado incumple el modo agregado.')
    require(len(results['periods'])==len(config['periods']),'Faltan periodos.')
    hr = set(inc.hr_candidates(config))
    qvoice = set(inc.q_candidates(config))
    require('ios_12m' not in hr and len(hr)==41 and len(qvoice)==51,'Cambió el catálogo V11.')
    statistics = Counter()
    for row in results['periods']:
        key = row['period']['id']
        candidates = row['candidates']
        require({r['feature'] for r in candidates if r['family']=='RH'}==hr,'Faltan pruebas RH: '+key)
        if key in config['qvoice']['period_ids']:
            for anchor in ['B','B_RH']:
                require({r['feature'] for r in candidates if r['family']=='QVoice' and r['anchor']==anchor}==qvoice,
                        'Faltan pruebas QVoice: '+key+' / '+anchor)
        require(max(row['roundtrip_maximum_difference'].values())<=1e-10,'Falló la serialización externa.')
        for candidate in candidates:
            statistics[candidate['family']+'_external_attempts']+=1
            statistics[candidate['family']+'_'+candidate['status']]+=1
            if candidate['status']=='ok':
                require(math.isfinite(candidate['metrics']['log_loss']),'Métrica no finita.')
                if candidate['family']=='RH' and not candidate['training_support']['eligible_for_selection']:
                    statistics['RH_insufficient_support']+=1
    for path in (out/'selection').glob('*.json'):
        selection = base.read(path)
        split = selection['split']
        require(split['training_last_label_end']<=split['validation_first'],'Solapamiento de reserva interna.')
        require(split['validation_last_outcome']<=split['cutoff'],'Outcome interno aún desconocido.')
        winner = selection['winner']
        require(winner['status']=='ok' and winner.get('eligible_for_selection',True),'Se eligió una candidata no elegible.')
        require(len(winner['additions'])<=3,'Se excedieron tres incorporaciones.')
        require(not selection['external_outcomes_used_for_selection'],'Selección externa en '+path.name)
        if 'candidate_availability' in selection:
            require(set(selection['candidate_availability'])==hr,'Falta soporte de alguna candidata RH.')
            for feature in winner['additions']:
                support = selection['candidate_availability'][feature]
                require(support['eligible_for_selection'] and support['observable_training_snapshots']>=6,
                        'Historia insuficiente para una ganadora RH.')
        elif winner['kind']=='q' and any(f!='qv_availability' for f in winner['additions']):
            require(winner.get('content_improves_availability') is True,'Contenido sin mejora del control de disponibilidad.')
        statistics['selection_files']+=1
    for path in (out/'models').glob('*.json'):
        artifact = base.read(path)
        hr_artifact = artifact.get('base',artifact)
        require(set(inc.B_TERMS)<=set(hr_artifact['model']['features']),'Artefacto sin B completo.')
        require(not artifact['employee_level_rows_persisted'] and not artifact['individual_scores_published'],
                'Artefacto fuera del modo agregado.')
        require('ios_12m' not in hr_artifact['model']['features'],'IOS apareció en un modelo.')
        statistics['model_files']+=1
    for relative,digest in manifest['source_hashes'].items():
        require(base.sha(base.ROOT/relative)==digest,'Cambió una fuente congelada: '+relative)
    for relative,digest in manifest['files'].items():
        require(base.sha(out/relative)==digest,'Cambió un artefacto registrado: '+relative)
    require(base.read(out/'preserved-models-before.json')==base.read(out/'preserved-models-after.json'),
            'Cambió un modelo anterior.')
    print(json.dumps({'outcome':'pass','run_id':results['run_id'],
        'manifest_sha256':base.sha(out/'manifest.json'),'statistics':dict(statistics),
        'employee_level_rows_persisted':False},ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
