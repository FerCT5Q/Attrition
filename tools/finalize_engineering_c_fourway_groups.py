"""Reconcilia artefactos agregados; no consulta datos ni vuelve a ajustar modelos."""
import csv
import hashlib
import itertools
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/analysis/engineering/20261008/c-fourway-groups-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    result = read(OUT / 'results.json')
    config = read(OUT / 'frozen-config.json')
    manifest = read(OUT / 'manifest.json')
    checks = []

    def check(claim, outcome, **metrics):
        checks.append({'afirmacion': claim, 'outcome': 'pass' if outcome else 'fail', **metrics})
        if not outcome:
            raise RuntimeError(claim)

    def close(a, b):
        return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9)

    check('Hashes del manifest recibido', all(sha(OUT / p) == h for p, h in manifest['files'].items()), archivos=len(manifest['files']))
    frozen = read(OUT / 'frozen-sources.json')
    check('Fuentes archivadas coinciden con originales y hashes', all(sha(ROOT / p) == h == sha(OUT / 'source' / p) for p, h in frozen.items()), archivos=len(frozen))
    preservation = read(OUT / 'preservation.json')
    check('Artefactos anteriores conservados', all(sha(ROOT / p) == h for p, h in preservation['files'].items()), archivos=len(preservation['files']))
    check('Configuracion congelada coincide', config == read(ROOT / 'config/engineering_c_fourway_groups_20261008.json'))

    folds = result['folds']
    variants = list(result['summary']['30'])
    base = folds[0]['selections']['C_current']['definition']
    candidate_count = 0
    for fold in folds:
        index = fold['fold']
        check(f'Periodo {index}: fold persistido coincide', fold == read(OUT / 'folds' / f'fold-{index}.json'))
        candidates = read(OUT / 'development-candidates' / f'fold-{index}.json')
        candidate_count += len(candidates)
        dimensions = {d for c in candidates for d in c['dimensions']}
        combinations = {tuple(sorted(c['dimensions'])) for c in candidates}
        expected = set(itertools.combinations(sorted(dimensions), config['combination_size']))
        check(f'Periodo {index}: cruces completos del espacio registrado', combinations == expected and len(combinations) == len(candidates) == fold['candidate_count'], cruces=len(candidates))
        check(f'Periodo {index}: orden temporal', fold['development']['latest_outcome'] < fold['origin'] <= fold['first_snapshot'] <= fold['last_snapshot'] < fold['latest_outcome'] <= result['knowledge_boundary'])
        for name in variants[1:]:
            pool = [c for c in candidates if c['admissible']]
            check(f'Periodo {index}: restricciones admisibles {name}', all(c['maximum_eligible_groups'] <= config['maximum_development_groups_each_snapshot'] and c['minimum_eligible_fraction'] >= config['minimum_development_eligible_fraction_each_snapshot'] for c in pool))
            if name == 'C_plus1':
                pool = [c for c in pool if set(base['dimensions']).issubset(c['dimensions'])]
            elif name == 'C_near40':
                low, high = config['target_group_range']
                pool = [c for c in pool if low <= c['mean_eligible_groups'] <= high]
            choice = fold['selections'][name]
            if not pool:
                check(f'Periodo {index}: fallback {name}', choice['fallback'] and choice['definition'] == base)
                continue
            maximum = max(c['capture_percent'] for c in pool)
            near = [c for c in pool if c['capture_percent'] >= maximum * (1 - config['capture_relative_tolerance'])]
            error = min(c['excess_group_snapshot_mae_pp'] for c in near)
            near = [c for c in near if c['excess_group_snapshot_mae_pp'] <= error + config['error_tolerance_pp']]
            winner = min(near, key=lambda c: (c['mean_eligible_groups'], -c['capture_percent'], c['name']))
            check(f'Periodo {index}: ganador reproducido {name}', winner == choice['winner_metrics'] and not choice['fallback'] and choice['admissible_candidates'] == len(pool) and choice['candidates_after_tolerance'] == len(near))

    for capacity, summaries in result['summary'].items():
        for name, summary in summaries.items():
            rows = [f['evaluation'][name]['scenarios'][capacity]['metrics'] for f in folds]
            check(f'Medias de metricas {name}, capacidad {capacity}', all(close(value, mean(row[key] for row in rows)) for key, value in summary['metrics'].items()))
            check(f'Medias de estructura {name}, capacidad {capacity}', all(close(value, mean(f['evaluation'][name]['structure'][key] for f in folds)) for key, value in summary['structure'].items()))
            comparable = {key: mean(f['evaluation'][name]['scenarios'][capacity]['control_on_same_partition'][key] for f in folds) for key in summary['control_on_same_partition']}
            check(f'Control comparable {name}, capacidad {capacity}', all(close(value, comparable[key]) for key, value in summary['control_on_same_partition'].items()))
            if name == 'C_current':
                continue
            differences = [f['evaluation'][name]['scenarios'][capacity]['metrics']['capture_percent'] - f['evaluation']['C_current']['scenarios'][capacity]['metrics']['capture_percent'] for f in folds]
            interval = next(i for i in result['intervals'] if i['capacity'] == capacity and i['variant'] == name)
            guards = {key: summary['metrics'][key] <= value + config['error_tolerance_pp'] for key, value in comparable.items()}
            wins = sum(d > 1e-9 for d in differences)
            rule = interval['ci95_pp'][0] > 0 and wins >= 3 and all(guards.values())
            check(f'Diferencias y regla {name}, capacidad {capacity}', close(mean(differences), interval['difference_pp']) and interval == summary['comparison'] and summary['error_checks'] == guards and summary['winning_periods'] == wins and summary['meets_rule'] == rule)

    public, suppressed = 0, 0
    for evaluation in [f['evaluation'] for f in folds] + [result['extension']['evaluation']]:
        for name, entry in evaluation.items():
            for capacity, scenario in entry['scenarios'].items():
                metrics = scenario['metrics']
                check(f'Capacidad y control {name}, {capacity}', close(metrics['coverage_percent'], float(capacity)) and close(scenario['control_on_same_partition']['capture_percent'], evaluation['C_current']['scenarios'][capacity]['metrics']['capture_percent']))
                check(f'Prioridad agregada publicable {name}, {capacity}', metrics['distinct_people_with_event'] >= config['minimum_distinct_events'])
                for row in scenario['selected_groups']:
                    if row['observed_publishable']:
                        public += 1
                        check('Tasa de grupo publicable y error reconciliado', row['minimum_effective_people_selected_snapshot'] >= config['minimum_public_people_each_snapshot'] and row['distinct_people_with_event'] >= config['minimum_distinct_events'] and close(row['error_pp'], abs(row['predicted_percent'] - row['observed_percent'])))
                    else:
                        suppressed += 1
                        check('Tasa de grupo suprimida', all(k not in row for k in ['observed_percent', 'error_pp', 'distinct_people_with_event']))

    extension = result['extension']
    selected = read(OUT / 'selected-groupings.json')
    check('Ultima seleccion congelada coincide', selected['origin'] == folds[-1]['origin'] == extension['model_origin'] and selected['selections'] == folds[-1]['selections'])
    check('Foto adicional separada y madura', extension['snapshot'] > folds[-1]['last_snapshot'] and extension['snapshot'] < extension['followup_end'] <= result['knowledge_boundary'])
    with (OUT / 'grupos-prioritarios-febrero.csv').open(encoding='utf-8-sig', newline='') as handle:
        csv_rows = list(csv.DictReader(handle))
    check('CSV contiene los grupos agregados esperados', len(csv_rows) == sum(len(e['scenarios']['30']['selected_groups']) for e in extension['evaluation'].values()))
    check('CSV conserva tasas suprimidas vacias', all(row['observed_publishable'] != 'False' or not any(row[k] for k in ['observed_percent', 'error_pp', 'distinct_people_with_event']) for row in csv_rows))
    narrative = (OUT / 'informe.md').read_text(encoding='utf-8')
    check('Informe UTF-8 sin caracteres de reemplazo', '\ufffd' not in narrative and '\u00c3\u00a1' not in narrative)
    check('Cero reajustes y sin filas persistidas', result['hazard_refits'] == 0 and not result['employee_level_rows_persisted'] and not result['individual_scores_published'])

    stamp = datetime.now(timezone.utc).isoformat()
    write(OUT / 'artifact-checks.json', {'fecha': stamp, 'outcome': 'pass', 'metodo': 'Reconciliacion independiente de JSON/CSV agregados y SHA256, sin consultar ni cargar filas de personas.', 'alcance': 'Los intervalos se contrastan con la evidencia guardada; no se vuelve a ejecutar bootstrap.', 'cruces': candidate_count, 'filas_agregadas_publicables': public, 'filas_agregadas_con_tasa_suprimida': suppressed, 'checks': checks})
    for source in [ROOT / 'docs/context/model-c-fourway-groups.md', Path(__file__)]:
        destination = OUT / 'source' / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    manifest['status'] = 'completed_analysis_report_and_artifact_reconciliation'
    manifest['files'] = {str(p.relative_to(OUT)): sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
    write(OUT / 'manifest.json', manifest)
    print(json.dumps({'outcome': 'pass', 'checks': len(checks), 'candidates': candidate_count, 'preserved_files': len(preservation['files']), 'manifest_files': len(manifest['files'])}))


if __name__ == '__main__':
    main()
