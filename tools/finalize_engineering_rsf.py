"""Reconciliacion de evidencia agregada y parametros archivados del RSF."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import shutil
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/analysis/engineering/20261008/random-survival-forest-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []
    def check(claim,okay,**metrics):
        checks.append({'afirmacion':claim,'outcome':'pass' if okay else 'fail',**metrics})
        if not okay:
            raise RuntimeError(claim)
    config = read(OUT/'frozen-config.json')
    manifest = read(OUT/'manifest.json')
    check('Integridad del manifest recibido',all(sha(OUT/p)==h for p,h in manifest['files'].items()))
    preserved = read(OUT/'preservation.json')['files']
    check('Modelos y variantes anteriores conservados',all(sha(ROOT/p)==h for p,h in preserved.items()),archivos=len(preserved))
    sources = read(OUT/'frozen-sources.json')
    check('Fuentes congeladas coinciden',all(sha(ROOT/p)==h==sha(OUT/'source'/p) for p,h in sources.items()))
    bq = read(OUT/'bq-input-reconciliation.json')
    check('Contrato BQ alineado con etiqueta mensual y episodios iguales',bq['outcome']=='pass' and
          all(bq[k]==0 for k in ['unmatched_rows','extra_rows','duplicate_rows']) and
          all(v==0 for v in bq['invariant_mismatch_counts'].values()) and sha(ROOT/bq['query'])==bq['sql_sha256'])
    label_audit = read(OUT/'bq-label-contract-audit.json')
    check('Diferencia R6 explicada por registro y audit independiente',label_audit['outcome']=='pass' and
          bq['label_contract_counts']==label_audit['metrics'] and sha(ROOT/label_audit['query'])==label_audit['sql_sha256'])
    for period in ['aug_dec_2025','jan_feb_2026']:
        reconciliation = read(OUT/'qvoice-comparison'/f'{period}-reconciliation.json')
        check('BQ y sus calibraciones reproducen las metricas archivadas',
              set(reconciliation)=={'BQ','BQ_scalar','BQ_monthly_calibrated'} and
              all(r['outcome']=='pass' and max(abs(v) for v in r['differences'].values())<=1e-8 for r in reconciliation.values()),periodo=period)
    visual = read(OUT/'visual-review.json')
    check('Figuras revisadas y coherentes con la evidencia',visual['outcome']=='pass' and
          all(sha(OUT/p)==h for p,h in visual['png_sha256'].items()))
    for kind in ['historical','qvoice']:
        result = read(OUT/f'{kind}-results.json')
        periods = result['periods']
        for name,entry in result['summary'].items():
            for metric,value in entry['global'].items():
                expected = sum(p['evaluation'][name]['global'][metric] for p in periods)/len(periods)
                check('Media global reconciliada',math.isclose(value,expected,rel_tol=1e-10,abs_tol=1e-10))
            for cap,metrics in entry['scenarios'].items():
                for metric,value in metrics.items():
                    expected = sum(p['evaluation'][name]['scenarios'][cap]['metrics'][metric] for p in periods)/len(periods)
                    check('Media de prioridad reconciliada',math.isclose(value,expected,rel_tol=1e-10,abs_tol=1e-10))
        for period in periods:
            check('Seguimiento evaluado maduro',period['latest_outcome']<=config['knowledge_boundary'])
            for entry in period['evaluation'].values():
                for cap,scenario in entry['scenarios'].items():
                    check('Capacidad conservada',abs(scenario['metrics']['coverage_percent']-float(cap))<1e-8)
                    for row in scenario['selected_groups']:
                        if row['observed_publishable']:
                            check('Tasa publicable con minimos',row['minimum_effective_people_selected_snapshot']>=30 and row['distinct_people_with_event']>=30)
                        else:
                            check('Tasa suprimida sin observado',all(k not in row for k in ['observed_percent','error_pp','distinct_people_with_event']))
    tree_count = 0
    for target in [p.parent for p in (OUT/'folds').glob('*/model.json')]+[OUT/'trained-model']:
        model = read(target/'model.json')
        selection = read(target/'selection.json')
        check('Calibracion anterior al origen',model['calibration']['latest_outcome']<model['origin'])
        candidates = selection['candidates']
        highest = max(c['priority']['capture_percent'] for c in candidates)
        close = [c for c in candidates if c['priority']['capture_percent']>=highest*(1-config['capture_relative_tolerance'])]
        winner = min(close,key=lambda c:(c['global']['log_loss'],c['priority']['group_snapshot_mae_pp'],-c['min_samples_leaf'],c['id']))
        check('Seleccion reproducida de candidatos guardados',winner==selection['winner'] and winner==model['specification'],candidatos=len(candidates))
        check('Exportacion de inferencia reconciliada',read(target/'serialization-check.json')['outcome']=='pass')
        with np.load(target/'forest-parameters.npz',allow_pickle=False) as arrays:
            check('Contenido limitado a parametros',set(arrays.files)=={f'{f}{i}' for i in range(model['trees']) for f in ['f','l','r','t','s']})
            for i in range(model['trees']):
                left,right,curves = arrays[f'l{i}'],arrays[f'r{i}'],arrays[f's{i}']
                check('Curvas finitas, acotadas y no crecientes',np.isfinite(curves).all() and (curves>=0).all() and (curves<=1+1e-12).all() and (np.diff(curves,axis=1)<=1e-12).all())
                inner = np.flatnonzero(left>=0)
                check('Arbol sin ciclos y con hijos validos',(left[inner]>inner).all() and (right[inner]>inner).all() and (left[inner]<len(left)).all() and (right[inner]<len(left)).all())
                tree_count += 1
    compact = [record for p in OUT.glob('**/compact-bootstrap-checks.json') for record in read(p)]
    check('Compactacion bootstrap equivalente en registros guardados',bool(compact) and all(c['outcome']=='pass' and c['same_splits'] and c['maximum_curve_difference']<1e-10 for c in compact),registros_con_repeticiones=len(compact))
    info = {'fecha':datetime.now(timezone.utc).isoformat(),'outcome':'pass','metodo':'Reconciliacion de agregados, reglas temporales, selecciones, parametros de inferencia y SHA256; sin cargar filas ni reajustar modelos.',
            'arboles_de_modelos_finales_e_historicos':tree_count,'checks':checks}
    (OUT/'artifact-checks.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    target = OUT/'source/tools'/Path(__file__).name
    shutil.copy2(Path(__file__),target)
    manifest['status'] = 'completed_analysis_report_and_artifact_reconciliation'
    manifest['files'] = {str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'outcome':'pass','checks':len(checks),'trees':tree_count,'preserved_files':len(preserved)}))


if __name__=='__main__':
    main()
