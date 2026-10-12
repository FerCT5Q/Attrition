"""Comprueba resultados agregados y parámetros del experimento B + QVoice."""
import argparse
import itertools
import json
import math
import platform
from importlib import metadata
from pathlib import Path

from qvoice_model_data import ROOT, load_config, sha256_file, utc_now, write_json


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def verify(root):
    config = load_config(root / 'experiment-config.yaml')
    comparison = read(root / 'comparison-results.json')
    checks, searches = [], []

    def check(name, condition):
        checks.append({'check': name, 'passed': bool(condition)})

    blocks = list(config['search']['blocks'])
    expected = {
        ('+'.join(group), l2)
        for size in range(1, len(blocks) + 1)
        for group in itertools.combinations(blocks, size)
        for l2 in config['search']['l2_grid']
    }
    expected |= {(f'pca_{k}', l2) for k in config['search']['pca_components']
                 for l2 in config['search']['l2_grid']}
    directories = [(root / 'folds' / p['id'], p['start'])
                   for p in config['validation']['main_periods']]
    directories.append((root / 'trained-model', config['knowledge_boundary']))
    for directory, cutoff in directories:
        selected = read(directory / 'selection.json')
        model = read(directory / 'model.json')
        trials = selected['trials']
        eligible = [r for r in trials if r['converged'] and r['monthly_brier'] is not None]
        winner = min(eligible, key=lambda r: (r['monthly_brier'], r['parameters'], r['l2'], r['id']))
        check(f'{directory.name}: rejilla completa sin duplicados',
              len(trials) == len(expected) and {(r['id'], r['l2']) for r in trials} == expected)
        check(f'{directory.name}: selección reproducida', winner == selected['selected'] == model['selected'])
        check(f'{directory.name}: selección anterior a calibración',
              selected['maximum_training_label_end'] <= min(selected['selection_dates'])
              and max(selected['selection_dates']) < min(model['calibration_snapshots'])
              and model['maximum_fit_label_end'] <= min(model['calibration_snapshots'])
              and model['maximum_calibration_label_end'] <= cutoff)
        base = model['base']
        correction = model['correction']
        encoder = correction['encoder']
        dimension = (len(encoder['columns']) if correction['kind'] == 'blocks'
                     else 1 + encoder['components'] + len(encoder['features']))
        check(f'{directory.name}: dimensiones y parámetros finitos',
              len(base['beta']) == len(base['encoder']['columns'])
              and len(correction['beta']) == dimension
              and all(math.isfinite(v) for v in base['beta'] + correction['beta']))
        cal = model['calibration']
        lo, hi = config['search']['calibration']['slope_bounds']
        check(f'{directory.name}: convergencia y calibración',
              correction['converged'] and cal['converged']
              and math.isfinite(cal['intercept']) and lo <= cal['slope'] <= hi)
        searches.append({'stage': directory.name, 'attempts': len(trials),
                         'converged': len(eligible), 'selected': winner['id'],
                         'best_pca': min((r for r in eligible if r['kind'] == 'pca'),
                                         key=lambda r: r['monthly_brier'])})

    metric_names = ('pr_auc', 'lift_at_10_percent', 'brier_score',
                    'calibration_error_pp', 'top_quintile_calibration_error_pp')
    baseline_reference = read(root / 'inputs/baseline-control-reference.json')
    baseline_periods = {p['period']: p['control'] for p in baseline_reference['periods']}
    check('Fuente de B preservada', sha256_file(ROOT / baseline_reference['source']) == baseline_reference['source_sha256'])
    for p in comparison['periods']:
        models = [p[k] for k in ('control', 'base_calibrated', 'availability', 'uncalibrated', 'response')]
        check(f'{p["period"]}: misma cohorte y métricas finitas',
              p['cohort_equality_verified'] and p['people'] >= 30
              and len({m['exposures'] for m in models}) == 1
              and len({m['event_exposures'] for m in models}) == 1
              and all(math.isfinite(m[k]) for m in models for k in metric_names))
        reconciliation = p['control_reconciliation']
        check(f'{p["period"]}: diferencias de B recalculadas desde su fuente',
              all(abs((p['control'][k] - baseline_periods[p['period']][k]) - v) < 1e-12
                  for k, v in reconciliation.items()))
        check(f'{p["period"]}: reproducción de B',
              reconciliation['exposures'] == reconciliation['event_exposures'] == 0
              and all(abs(reconciliation[k]) <= max(abs(p['control'][k]) * .01, 1e-10)
                      for k in ('pr_auc', 'lift_at_10_percent', 'brier_score')))
        check(f'{p["period"]}: bootstrap completo y ordenado',
              p['uncertainty']['repetitions'] == config['validation']['bootstrap_repetitions']
              and all(math.isfinite(i['lower']) and math.isfinite(i['upper']) and i['lower'] <= i['upper']
                      for pair in p['uncertainty']['paired_differences'].values() for i in pair.values()))
    # Recalcular las reglas desde las métricas, sin llamar a la función de decisión.
    reproduced = {}
    for ref in ('control', 'availability'):
        reproduced[f'ranking_vs_{ref}'] = all(p['response']['pr_auc'] > p[ref]['pr_auc']
            and p['response']['lift_at_10_percent'] > p[ref]['lift_at_10_percent'] for p in comparison['periods'])
        for metric in metric_names[2:]:
            reproduced[f'{metric}_vs_{ref}'] = sum(p['response'][metric] for p in comparison['periods']) <= sum(p[ref][metric] for p in comparison['periods'])
    check('Regla conjunta reproducida', reproduced == comparison['decision']['checks'])
    check('Estado de decisión coherente', comparison['decision']['status'] ==
          ('prometedora' if all(reproduced.values()) else 'sin mejora demostrada'))
    contract = read(root / 'execution-contract.json')
    check('Código de entrenamiento conservado', sha256_file(ROOT / 'tools/qvoice_calibrated_model.py') == contract['implementation_sha256'])
    check('Copia de código de entrenamiento conservada', sha256_file(root / 'inputs/qvoice_calibrated_model.py') == contract['implementation_sha256'])
    check('Informe y figura disponibles', (root / 'informe-modelo-b-qvoice-calibrado.md').is_file()
          and (root / 'charts/comparacion-con-b.png').is_file())
    output = {'created_at': utc_now(), 'reporting_mode': 'presentation',
              'status': 'verified' if all(c['passed'] for c in checks) else 'failed',
              'checks': checks, 'searches': searches, 'employee_rows_read': 0,
              'environment': {'python': platform.python_version(),
                              **{p: metadata.version(p) for p in ('numpy', 'pandas', 'scipy', 'openpyxl', 'matplotlib', 'PyYAML', 'threadpoolctl')}},
              'scope': 'Reconciliación de artefactos agregados; no vuelve a entrenar ni reevalúa scores de variables.'}
    target = root / 'validation/artifact-checks.json'
    write_json(target, output)
    manifest = read(root / 'manifest.json')
    manifest['aggregate_validation'] = str(target.relative_to(root)).replace('\\', '/')
    manifest['aggregate_validation_status'] = output['status']
    manifest['artifact_sha256'][manifest['aggregate_validation']] = sha256_file(target)
    manifest['code_sha256']['tools/verify_qvoice_calibrated_artifacts.py'] = sha256_file(Path(__file__))
    write_json(root / 'manifest.json', manifest)
    print(json.dumps({'status': output['status'], 'checks': len(checks), 'searches': searches}, ensure_ascii=False))
    if output['status'] != 'verified':
        raise ValueError('Fallaron comprobaciones de artefactos; revisar validation/artifact-checks.json.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root', type=Path, required=True)
    verify(parser.parse_args().run_root.resolve())
