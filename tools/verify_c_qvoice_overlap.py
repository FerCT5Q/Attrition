"""Comprobaciones de agregados y parámetros del experimento CQ; sin DB."""
from pathlib import Path
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
import numpy as np
from qvoice_model_data import favorable_band

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT/'output/analysis/engineering/20261009/c-qvoice-overlap-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main(out):
    checks = []
    def check(claim, okay):
        checks.append({'claim': claim, 'outcome': 'pass' if okay else 'fail'})
    result = read(out/'results.json')
    previous = read(out/'preservation-before.json')
    for path, digest in previous.items():
        check('Preservado '+path, sha(ROOT/path) == digest)
    for file in out.rglob('*-derivation.json'):
        d = read(file)
        check('Partición de componentes '+str(file.relative_to(out)),
              len(d['remaining_items']) == d['denominator'] and
              not set(d['remaining_items']) & set(d['excluded_items']) and
              len(set(d['remaining_items']) | set(d['excluded_items'])) == 33)
        check('Reconciliación de media '+d['feature'], d['mismatch_count'] == 0 and
              d['original_mean_mismatch_count'] == 0 and d['eligibility_changed_count'] == 0 and
              d['matched_count'] == d['comparable_count'])
        n = d['denominator']
        for total in range(n+1):
            expected = ('100' if total == n else '<50' if total/n < .5 else '50–69' if total/n < .7
                        else '70–79' if total/n < .8 else '80–89' if total/n < .9 else '90–99')
            check(f'Frontera {n} componentes / {total} favorables',
                  favorable_band([1]*total+[0]*(n-total), required_count=n) == expected)
        check('Nulo no es desfavorable '+d['feature'], favorable_band([None]+[0]*(n-1), required_count=n) is None)
    for name, stats in result['summary'].items():
        for cap in ['20', '30', '40']:
            for metric, number in stats['scenarios'][cap].items():
                expected = np.mean([p['evaluation'][name]['scenarios'][cap]['metrics'][metric] for p in result['periods']])
                check(f'Media temporal {name}/{cap}/{metric}', abs(number-expected) <= 1e-10)
            check(f'Capacidad {name}/{cap}', abs(stats['scenarios'][cap]['coverage_percent']-int(cap)) <= 1e-8)
    for period in result['periods']:
        check('CQ histórico sin media '+period['id'], period['archived_mean_included'] is False)
        r = read(out/'folds'/period['id']/'reconciliation.json')
        check('Reproducción archivada '+period['id'], r['outcome'] == 'pass' and all(x['pass'] for x in r['checks']))
    for file in out.rglob('collinearity.json'):
        d = read(file)
        for sample in ['all_rows', 'complete_person_wave']:
            row = d[sample]
            check('Rango válido '+str(file.relative_to(out))+'/'+sample, 0 <= row['rank'] <= row['columns'])
            check('VIF de singular no identificable '+str(file.relative_to(out))+'/'+sample,
                (row['rank'] == row['columns']) or (row['vif_max'] is None and row['condition_number'] is None))
    for file in list((out/'folds').glob('*/*/model.json'))+list((out/'trained-model').glob('*/model.json')):
        artifact = read(file)
        check('Coeficientes y columnas '+str(file.relative_to(out)), len(artifact['beta']) == len(artifact['encoder']['columns']))
        check('Ajuste anterior al corte '+str(file.relative_to(out)), artifact['fit_maximum_label_end'] <= artifact['cutoff'])
        check('Selección anterior al corte '+str(file.relative_to(out)), max(artifact['selection_snapshots']) < artifact['cutoff'])
    for name, verdict in result['decisions'].items():
        check('Regla conjunta '+name, verdict['passes_comparable_checks'] == all(verdict['checks'].values()))
    check('Modelo final sin evaluación posterior atribuida', result['final_model_has_post_fit_validation'] is False)
    check('C sin reajuste', result['base_refits'] == 0)
    check('Sin periodos independientes inventados', result['new_independent_periods'] == 0)
    check('Sin filas persistidas', result['employee_level_rows_persisted'] is False)
    def finite(value):
        if isinstance(value, dict):
            return all(finite(v) for v in value.values())
        if isinstance(value, list):
            return all(finite(v) for v in value)
        return not isinstance(value, float) or math.isfinite(value)
    check('Agregados finitos', finite(result))
    report = {'date': datetime.now(timezone.utc).isoformat(), 'outcome': 'pass' if all(x['outcome']=='pass' for x in checks) else 'fail',
              'count': len(checks), 'checks': checks}
    (out/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    manifest = {'run': str(out.relative_to(ROOT)), 'outcome': report['outcome'],
        'reporting_mode': 'presentation', 'employee_level_rows_persisted': False,
        'authorization': result['authorization'], 'files': {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file() and p.name != 'manifest.json'}}
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'outcome': report['outcome'], 'checks': len(checks), 'preserved_files': len(previous)}, ensure_ascii=False))
    if report['outcome'] != 'pass':
        raise RuntimeError('Falló una comprobación; revisar verification.json.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=DEFAULT)
    main(parser.parse_args().output)
