"""Cierra la evaluación completa; archiva el modelo probado si C no supera B."""
from pathlib import Path
from datetime import datetime,timezone
import shutil
from engineering_model_c import ROOT,read,write,sha


def main():
    cfg=read(ROOT/'config/engineering_model_c_20261008_fast.json');out=ROOT/cfg['output']
    result=read(out/'evaluation.json')
    if result['decision']['passes_all'] or len(result['folds'])!=4:
        raise RuntimeError('Este cierre requiere cuatro periodos completos y regla de promoción no superada.')
    if (out/'results.json').exists():
        raise RuntimeError('Los resultados finales ya existen.')
    last=result['folds'][-1]
    artifact=read(out/'folds'/f'fold-{last["fold"]}-C-model.json')
    artifact.update({'status':'experimental_not_promoted','training_cutoff':last['origin'],
                     'latest_training_label':last['train_latest_label'],
                     'evaluation_knowledge_boundary':cfg['knowledge_boundary'],
                     'empirical_decision':result['decision']['status']})
    write(out/'trained-model/model-c.json',artifact)
    groups=last['group_definition'].copy()
    groups['rules']=[{**r,'node':int(r['node'])} for r in groups['rules']]
    groups['high_nodes']=[int(n) for n in groups['high_nodes']]
    write(out/'trained-model/groups.json',groups)
    stopped=datetime.now(timezone.utc)
    start=(out/'frozen-config.json').stat().st_mtime
    load=(out/'population.json').stat().st_mtime-start
    traces=[read(p) for p in (out/'selection').glob('fold-*.json')]
    result.update({'final_features':last['C_features'],'final_l2':last['C_l2'],
                   'final_model_refit':False,'final_training_cutoff':last['origin'],
                   'forecast_snapshot':None,'forecast_groups':[],
                   'elapsed_seconds':stopped.timestamp()-start,'load_seconds':load,
                   'completed_evaluation_seconds':load+sum(f['elapsed_seconds'] for f in result['folds']),
                   'hazard_fits':sum(t['fits'] for t in traces)+2*len(result['folds']),
                   'hazard_fits_count_kind':'requested_evaluations','employee_level_rows_persisted':False,
                   'individual_scores_published':False,'qvoice_included':False})
    write(out/'results.json',result)
    write(out/'finalization.json',{'recorded_at':stopped.isoformat(),
         'status':'evaluación completa; modelo experimental archivado',
         'comparison_completed':True,'four_external_periods_completed':True,
         'final_refit_completed':False,'final_search_stopped':True,
         'reason':'C no supera la regla de promoción y apenas cambia la identificación de los grupos interpretables. Se detiene la selección adicional para un reajuste a septiembre de 2026; se conserva la última especificación realmente evaluada. No cambian métricas, selección de los cuatro periodos ni regla de decisión.',
         'saved_model_training_cutoff':last['origin'],
         'plan_deviation':'El plan contemplaba un reajuste adicional aun sin promoción. Se omite al cerrar la comparación para evitar más cómputo sin una mejora suficiente para el objetivo; no se publican pronósticos actuales.',
         'C_plus_Q_started':False,'code_sha256':sha(Path(__file__))})
    write(out/'manifest.json',{'run_id':cfg['run_id'],'reporting_mode':'presentation','authorization':cfg['authorization'],
         'status':'completed_evaluation_not_promoted','employee_level_rows_persisted':False,
         'individual_scores_published':False,'salt_persisted':False,'executed_at':stopped.isoformat(),
         'final_model_training_cutoff':last['origin'],'final_refit_completed':False,
         'elapsed_seconds':result['elapsed_seconds'],
         'files':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'}})
    print('Comparación completa cerrada; C experimental archivado con su fecha real de entrenamiento.')


if __name__=='__main__':
    main()
