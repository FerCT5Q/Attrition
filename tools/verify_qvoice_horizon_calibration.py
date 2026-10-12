"""Verificación independiente de artefactos agregados de calibración R6."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def verify(root):
    read = lambda path: json.loads(path.read_text(encoding='utf-8-sig'))
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = read(root/'manifest.json')
    result = read(root/'comparison-results.json')
    details = read(root/'calibration-details.json')
    history = read(root/'calibration-history.json')['rows']
    contract = read(root/'execution-contract.json')
    settings = read(root/'inputs/qvoice_horizon_calibration_20261008.json')
    scalar = read(root/'trained-model/scalar-model.json')
    uncal = read(root/'trained-model/uncalibrated-model.json')
    source_final = read(ROOT/settings['source_run']/'trained-model/model.json')
    checks = []

    def check(name, passed):
        checks.append({'check': name, 'passed': bool(passed)})

    check('completed', manifest['status'] == 'completed')
    check('privacy_mode', manifest['reporting_mode'] == 'presentation' and
          all(manifest[key] is False for key in ['employee_level_rows_persisted', 'individual_scores_published', 'disk_cache_of_rows']))
    check('all_artifact_hashes', all(digest(root/path) == value for path, value in manifest['artifacts_sha256'].items()))
    check('source_run_immutable', all(digest(ROOT/path) == value for path, value in contract['source_artifacts'].items()))
    check('input_snapshots_match', all(digest(root/'inputs'/Path(path).name) == value for path, value in contract['inputs'].items()))
    check('retained_base_and_qvoice_coefficients', source_final['base'] == uncal['base'] and source_final['correction'] == uncal['correction'])
    check('identity_model', uncal['calibration'] == {'intercept': 0., 'slope': 1.})
    check('scalar_base_hash', digest(root/'trained-model'/scalar['uncalibrated_model']) == scalar['uncalibrated_model_sha256'])
    check('final_scalar_metadata', scalar['calibration'] == next(c for c in details if c['target'] == 'final'))
    check('same_global_cutoff', result['knowledge_boundary'] == scalar['knowledge_boundary'] == settings['knowledge_boundary'])
    check('sql_hash', digest(ROOT/result['query']) == result['query_sha256'])
    check('ephemeral_sql_salt', '__RUN_SALT__' in (ROOT/result['query']).read_text(encoding='utf-8'))
    check('all_calibration_labels_mature', all(pd.Timestamp(d)+pd.DateOffset(months=6) <= pd.Timestamp(c['cutoff']) for c in details for d in c['origins']))
    check('all_fits_historical', all(pd.Timestamp(r['maximum_training_label_end']) < pd.Timestamp(r['origin']) for r in history))
    check('all_auxiliary_converged', all(r['converged'] for r in history))
    check('minimum_calibration_origins', all(len(c['origins']) >= settings['minimum_calibration_origins'] for c in details if c['status'] == 'fitted'))
    check('fallback_is_identity', all(c['log_multiplier'] == 0 and c['multiplier'] == 1 for c in details if c['status'] != 'fitted'))
    check('fit_objective_nonworsening', all(c['scalar_fit_log_loss'] <= c['identity_fit_log_loss'] for c in details if c['status'] == 'fitted'))
    check('prediction_equivalence', result['benchmark']['maximum_absolute_difference'] <= 1e-12)
    check('auxiliary_privacy', all(r['training_people'] >= 30 and r['training_event_exposures'] >= 30 and r['metrics']['event_exposures'] >= 30 for r in history))
    check('test_privacy', all(r['people'] >= 30 and r['metrics']['control']['event_exposures'] >= 30 for r in result['periods']))
    check('original_metrics_reproduced', all(abs(value) < 1e-8 for r in result['periods'] for values in r['reconciliation_errors'].values() for value in values.values()))
    check('ranking_preserved', all(r['rank_order_identical'] and all(abs(r['metrics']['scalar'][m]-r['metrics']['uncalibrated'][m]) < 1e-12 for m in ['pr_auc', 'lift_at_10_percent']) for r in result['periods']))
    check('same_cohorts_all_variants', all(len({m[k] for m in r['metrics'].values()}) == 1 for r in result['periods'] for k in ['exposures', 'event_exposures', 'observed_percent']))
    check('paired_bootstrap_point_differences', all(abs(v['difference']-(r['metrics'][v['left']][v['metric']]-r['metrics'][v['right']][v['metric']])) < 1e-12 for r in result['periods'] for v in r['paired_loss_intervals']))
    check('stored_gate_matches_metrics', all(passed == (next(r for r in result['periods'] if r['period'] == period)['metrics']['scalar'][metric] <= next(r for r in result['periods'] if r['period'] == period)['metrics']['uncalibrated'][metric]+1e-14) for period, group in result['checks'].items() for metric, passed in group.items()))
    output = {'status': 'passed' if all(c['passed'] for c in checks) else 'failed', 'check_count': len(checks), 'checks': checks}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if output['status'] != 'passed':
        raise SystemExit(1)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root', type=Path, default=ROOT/'output/analysis/engineering/20261008/qvoice-horizon-calibration-v1')
    parser.add_argument('--record', action='store_true', help='Registrar comprobaciones y pruebas sintéticas después de verificar.')
    args = parser.parse_args()
    outcome = verify(args.run_root)
    if args.record:
        sys.path.insert(0, str(ROOT/'tests'))
        suite = unittest.TestSuite([unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern=pattern)
                                   for pattern in ['test_qvoice_horizon_calibration.py', 'test_qvoice_calibrated_model.py']])
        test_result = unittest.TextTestRunner(verbosity=1).run(suite)
        outcome['synthetic_tests'] = {'tests_run': test_result.testsRun, 'failures': len(test_result.failures),
                                      'errors': len(test_result.errors), 'passed': test_result.wasSuccessful()}
        if not test_result.wasSuccessful():
            raise SystemExit(1)
        for path in [Path(__file__), ROOT/'tests/test_qvoice_horizon_calibration.py', ROOT/'tests/test_qvoice_calibrated_model.py']:
            shutil.copy2(path, args.run_root/'inputs'/path.name)
        outcome['verifier_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        (args.run_root/'independent-validation.json').write_text(json.dumps(outcome, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        manifest = json.loads((args.run_root/'manifest.json').read_text(encoding='utf-8'))
        manifest['independent_validation'] = 'independent-validation.json'
        manifest['artifacts_sha256'] = {str(p.relative_to(args.run_root)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in args.run_root.rglob('*') if p.is_file() and p.name != 'manifest.json'}
        (args.run_root/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
