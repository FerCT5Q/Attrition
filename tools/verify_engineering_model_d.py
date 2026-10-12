"""Verificación independiente de los artefactos agregados del modelo D."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT/'output/analysis/engineering/20261010/model-d-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(out):
    required = ['results.json','selection-decision.json','analysis-checks.json','manifest.json',
                'preservation.json','trained-model/model.json','trained-model/selection.json',
                'folds/aug_dec_2025/model.json','folds/jan_feb_2026/model.json']
    missing = [name for name in required if not (out/name).is_file()]
    manifest = read(out/'manifest.json')
    mismatches = {name: {'expected': digest, 'actual': sha(out/name) if (out/name).is_file() else None}
                  for name, digest in manifest['files'].items()
                  if not (out/name).is_file() or sha(out/name) != digest}
    result = read(out/'results.json')
    decision = read(out/'selection-decision.json')
    checks = read(out/'analysis-checks.json')
    preservation = read(out/'preservation.json')
    selections = [read(out/'folds'/p/'selection.json') for p in ['aug_dec_2025','jan_feb_2026']]
    rsf_checks = [read(out/'folds'/p/'rsf-qvoice'/'serialization-check.json')
                  for p in ['aug_dec_2025','jan_feb_2026']]
    models = [read(out/'folds'/p/'model.json') for p in ['aug_dec_2025','jan_feb_2026']]
    models.append(read(out/'trained-model'/'model.json'))
    forbidden = {'person_key','employee_id','email','y_next','y_6m','predictions'}
    parameter_key_violations = []
    for i, model in enumerate(models):
        text_keys = set()
        stack = [model]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                text_keys.update(str(k).lower() for k in value)
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
        overlap = sorted(forbidden & text_keys)
        if overlap:
            parameter_key_violations.append({'model_index': i, 'keys': overlap})
    independent = {
        'required_files_present': not missing,
        'manifest_hashes_match': not mismatches,
        'decision_matches_results': decision == result['decision'],
        'CQ_remains_selected': not decision['promote_D'],
        'history_query_reconciled': checks['history_query_reconciled_one_to_one'],
        'CQ_reproduced': checks['CQ_reproduced_at_1e8'],
        'D_serialized': checks['D_serialization_reproduced'],
        'prior_artifacts_unchanged': preservation['unchanged'] and checks['prior_artifacts_unchanged'],
        'RSF_serialization_passed': all(x['outcome'] == 'pass' and x['maximum_absolute_difference'] <= 1e-10 for x in rsf_checks),
        'no_employee_level_keys_in_model_parameters': not parameter_key_violations,
        'first_period_monthly_fallback_recorded': selections[0]['selection_mode'] == 'monthly_fallback',
        'second_period_r6_selection_recorded': selections[1]['selection_mode'] == 'r6',
        'privacy_flags': (not result['employee_level_rows_persisted'] and not result['individual_scores_published']
                          and not manifest['employee_level_rows_persisted'] and not manifest['individual_scores_published'])
    }
    report = {'outcome': 'pass' if all(independent.values()) else 'fail', 'checks': independent,
              'missing_files': missing, 'manifest_mismatches': mismatches,
              'parameter_key_violations': parameter_key_violations}
    (out/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT)
    args = parser.parse_args()
    report = verify(args.output.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(report['outcome'] != 'pass')
