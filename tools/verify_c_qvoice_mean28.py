"""Verifica agregados, procedencia y cortes temporales de CQ media28; sin DB."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
import math
import statistics

from qvoice_model_data import favorable_band

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT/'output/analysis/engineering/20261009/c-qvoice-mean28-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def finite(value):
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    if isinstance(value, list):
        return all(finite(v) for v in value)
    return not isinstance(value, float) or math.isfinite(value)


def main(out):
    checks = []

    def check(claim, okay):
        checks.append({'claim': claim, 'outcome': 'pass' if okay else 'fail'})

    def close(claim, actual, expected, tolerance=1e-10):
        check(claim, abs(actual-expected) <= tolerance)

    result = read(out/'results.json')
    config = read(out/'frozen-config.json')
    previous = read(out/'preservation-before.json')
    for path, digest in previous.items():
        check('Preservado '+path, (ROOT/path).is_file() and sha(ROOT/path) == digest)
    for file in (out/'source').rglob('*'):
        if file.is_file():
            current = ROOT/file.relative_to(out/'source')
            check('Fuente congelada '+str(file.relative_to(out)), current.is_file() and sha(file) == sha(current))
    check('Consulta guardada y ejecutada', result['source_query'] == config['query'] and
          sha(ROOT/config['query']) == result['source_query_sha256'])
    executions = read(out/'query-executions.json')
    check('Dos cargas anuales', [x['year'] for x in executions] == [2025, 2026])
    check('Hash SQL de ambas cargas', all(x['sql_sha256'] == result['source_query_sha256'] for x in executions))
    check('Etapa de selección explícita', result['stage'] == 'model_selection')
    check('Exploración histórica declarada', result['configuration_chosen_after_historical_exploration'] is True)
    check('Dos periodos externos', len(result['periods']) == 2)
    check('Predictores fijos', result['fixed_qvoice_items'] == config['fixed_qvoice_items'])

    expected_excluded = {'qv_M09', 'qv_M13', 'qv_M29', 'qv_M12', 'qv_M27'}
    all_items = {f'qv_M{i:02}' for i in range(1, 34)}
    derivations = list((out/'folds').glob('*/*-derivation.json'))
    check('Derivación disponible en cada periodo', len(derivations) == 2)
    for file in derivations:
        d = read(file)
        label = str(file.relative_to(out))
        check('Partición exacta de 33 componentes '+label,
              d['denominator'] == 28 and len(d['remaining_items']) == 28 and
              set(d['excluded_items']) == expected_excluded and
              set(d['remaining_items']) == all_items-expected_excluded)
        check('Reconciliación independiente '+label, d['outcome'] == 'pass' and
              d['mismatch_count'] == d['original_mean_mismatch_count'] == d['eligibility_changed_count'] == 0 and
              d['comparable_count'] == d['matched_count'] and d['comparable_count'] >= 30)
        check('Elegibilidad exige los 33 originales '+label, d['required_valid_original_items'] == 33)
    for n in [28, 33]:
        for total in range(n+1):
            expected = next((label for upper, label in [(50, '<50'), (70, '50–69'),
                (80, '70–79'), (90, '80–89'), (100, '90–99')] if 100*total < upper*n), '100')
            check(f'Banda {total}/{n}', favorable_band([1]*total+[0]*(n-total), required_count=n) == expected)
        check(f'Nulo distinto de desfavorable / {n}', favorable_band([None]+[0]*(n-1), required_count=n) is None)

    for summary_key, evaluation_key in [('summary', 'evaluation'), ('four_cuts_summary', 'four_cuts_evaluation')]:
        for name, stats in result[summary_key].items():
            for metric, value in stats['global'].items():
                close(f'Media global {summary_key}/{name}/{metric}', value,
                      statistics.mean(p[evaluation_key][name]['global'][metric] for p in result['periods']))
            for cap in ['20', '30', '40']:
                for metric, value in stats['scenarios'][cap].items():
                    close(f'Media de periodos {summary_key}/{name}/{cap}/{metric}', value,
                          statistics.mean(p[evaluation_key][name]['scenarios'][cap]['metrics'][metric] for p in result['periods']))
                close(f'Capacidad {summary_key}/{name}/{cap}', stats['scenarios'][cap]['coverage_percent'], int(cap), 1e-8)

    model_files = []
    for period in result['periods']:
        fold = out/'folds'/period['id']
        archive = read(ROOT/config['source_cq']/'folds'/period['id']/'evaluation.json')
        r = read(fold/'reconciliation.json')
        check('Reproducción C/CQ '+period['id'], r['outcome'] == 'pass' and all(x['pass'] for x in r['checks']))
        for name in ['C', 'CQ', 'C_availability']:
            for cap in ['20', '30', '40']:
                actual = period['evaluation'][name]['scenarios'][cap]['metrics']
                expected = archive['evaluation'][name]['scenarios'][cap]['metrics']
                for metric, value in expected.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        close(f'Archivo {period["id"]}/{name}/{cap}/{metric}', actual[metric], value, config['reconciliation_absolute_tolerance'])
        check('Mismas seis preguntas '+period['id'],
              [f for f in period['features'] if not f.startswith('qv_remaining_')] == config['fixed_qvoice_items'])
        check('Follow-up dentro del conocimiento '+period['id'], period['latest_outcome'] <= config['knowledge_boundary'])
        check('Mismo denominador '+period['id'], period['fixed_mean_denominator'] == 28)
        selection = read(fold/'selection.json')
        check('Combinación fija en selección '+period['id'], selection['best_archived_mean_candidate']['features'] == config['fixed_overlap_features'])
        check('Selección L2 sin outcomes externos '+period['id'], selection['selection_uses_outer_outcomes'] is False)
        model_files += list(fold.glob('*/model.json'))+[fold/'mean28-availability-model.json']
        for field in ['evaluation', 'four_cuts_evaluation']:
            for name, data in period[field].items():
                for cap, scenario in data['scenarios'].items():
                    close(f'Capacidad por periodo {period["id"]}/{field}/{name}/{cap}',
                          scenario['metrics']['coverage_percent'], int(cap), 1e-8)
                    for index, group in enumerate(scenario['selected_groups']):
                        label = f'{period["id"]}/{field}/{name}/{cap}/{index}'
                        if 'predicted_percent' in group:
                            check('Cohorte publicable '+label, group['minimum_effective_people_selected_snapshot'] >= 30)
                        if group['observed_publishable']:
                            check('Eventos publicables '+label, group['distinct_people_with_event'] >= 30)
                        else:
                            check('Tasa suprimida '+label, not {'observed_percent', 'error_pp', 'distinct_people_with_event'} & set(group))

    model_files.append(out/'trained-model/model-mean28.json')
    for file in model_files:
        artifact = read(file)
        label = str(file.relative_to(out))
        check('Coeficientes y columnas '+label, len(artifact['beta']) == len(artifact['encoder']['columns']))
        check('Etiquetas previas al corte '+label, artifact['fit_maximum_label_end'] <= artifact['cutoff'])
        check('Parámetros finitos '+label, finite(artifact))
        if 'selection_snapshots' in artifact:
            check('Selección previa al corte '+label, max(artifact['selection_snapshots']) < artifact['cutoff'])
        if 'trials' in artifact:
            check('L2 y convergencia '+label, sorted(x['l2'] for x in artifact['trials']) == config['l2_grid'] and
                  all(x['converged'] for x in artifact['trials']))
    for file in (out/'folds').glob('*/*/collinearity.json'):
        d = read(file)
        for sample in ['all_rows', 'complete_person_wave']:
            row = d[sample]
            label = str(file.relative_to(out))+'/'+sample
            check('Rango válido '+label, 0 <= row['rank'] <= row['columns'])
            check('Singularidad no oculta '+label, row['rank'] == row['columns'] or
                  (row['vif_max'] is None and row['condition_number'] is None))

    for interval in result['intervals']:
        a, b, metric = interval['left'], interval['right'], interval['metric']
        if metric.startswith('capture'):
            section, name = ('scenarios', metric[7:]), 'capture_percent'
            av = result['summary'][a][section[0]][section[1]][name]
            bv = result['summary'][b][section[0]][section[1]][name]
        else:
            av, bv = [result['summary'][n]['global'][metric] for n in [a, b]]
        close(f'Diferencia pareada {a}/{b}/{metric}', interval['difference'], av-bv)
        check(f'Intervalo ordenado {a}/{b}/{metric}', interval['ci95'][0] <= interval['ci95'][1])

    provenance = read(out/'trained-model/provenance.json')
    final = out/'trained-model/model-mean28.json'
    check('Copia final exacta', sha(final) == sha(ROOT/provenance['source']) == provenance['sha256'] == provenance['copy_sha256'])
    check('Final sin ajuste nuevo ni evaluación posterior', provenance['new_fit'] is False and provenance['post_fit_validation'] is False)
    check('Sin reajustes innecesarios', result['base_refits'] == result['final_refits'] == 0 and result['fit_count'] == 26)
    check('Sin filas ni scores individuales publicados', result['employee_level_rows_persisted'] is False and result['individual_scores_published'] is False)
    check('Sin cambio de scores de assessment', result['score_changes'] is False)
    check('Agregados finitos', finite(result))
    check('Decisión explícita', bool(read(out/'selection-decision.json')['conclusion']))
    with (out/'tabla-comparativa.csv').open(encoding='utf-8-sig', newline='') as f:
        table = list(csv.DictReader(f))
    check('Cinco comparadores en tabla', len(table) == 5)
    for row, name in zip(table, ['C', 'CQ', 'overlap', 'disjoint', 'items_only']):
        stats = result['summary'][name]
        close('Captura tabla '+name, float(row['captura_30_porcentaje']), stats['scenarios']['30']['capture_percent'])
        close('Error tabla '+name, float(row['error_grupo_mes_pp']), stats['scenarios']['30']['group_snapshot_mae_pp'])
        close('Pérdida tabla '+name, float(row['log_loss_por_1000']), stats['global']['log_loss']*1000)
        close('PR-AUC tabla '+name, float(row['pr_auc_porcentaje']), stats['global']['pr_auc']*100)
    outcome = 'pass' if all(c['outcome'] == 'pass' for c in checks) else 'fail'
    report = {'date': datetime.now(timezone.utc).isoformat(), 'outcome': outcome, 'count': len(checks),
              'scope': 'Agregados, contratos de derivación, parámetros, temporalidad y hashes; sin nueva consulta.', 'checks': checks}
    (out/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    completion = read(out/'completed.json')
    completion.update(status='complete' if outcome == 'pass' else 'verification_failed',
                      verification_count=len(checks), artifacts_completed_at=report['date'])
    (out/'completed.json').write_text(json.dumps(completion, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    manifest = {'run': str(out.relative_to(ROOT)), 'outcome': outcome, 'reporting_mode': 'presentation',
        'stage': result['stage'], 'employee_level_rows_persisted': False, 'authorization': result['authorization'],
        'files': {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file() and p.name != 'manifest.json'}}
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'outcome': outcome, 'checks': len(checks), 'preserved_files': len(previous)}, ensure_ascii=False))
    if outcome != 'pass':
        print(json.dumps([c for c in checks if c['outcome'] != 'pass'], ensure_ascii=False))
        raise RuntimeError('Revisar verification.json antes de entregar.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=DEFAULT)
    main(parser.parse_args().output)
