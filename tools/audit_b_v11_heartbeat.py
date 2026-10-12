"""Verifica encabezados ordinales del Heartbeat V11 sin leer respuestas."""
from datetime import datetime, timezone
import json

import engineering_model_c as base
from qvoice_model_data import inspect_sources, load_config

ROOT = base.ROOT
OUT = ROOT / 'output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence'


def main():
    target = OUT / 'v11-heartbeat-headers.json'
    if target.exists():
        raise RuntimeError('La evidencia existe; usar otra revisión.')
    config_path = ROOT / 'config/qvoice_model_calibrated_20261008.yaml'
    config = load_config(config_path)
    config['sources']['waves'] = [w for w in config['sources']['waves'] if w['year'] in {2024, 2025}]
    metadata = inspect_sources(config)
    rows = []
    for wave in metadata['waves']:
        indices = {key: wave['mapping'][key]['scale_indices'] for key in [f'Q{i}' for i in range(1, 54)]}
        matched = [key for key, values in indices.items() if len(values) == 1]
        missing = [key for key, values in indices.items() if not values]
        ambiguous = [key for key, values in indices.items() if len(values) > 1]
        rows.append({'year': wave['year'], 'file': wave['file'], 'sha256': wave['sha256'],
            'sheet': wave['sheet'], 'available_scale_bases': wave['scale_base_count'],
            'expected_scale_items': 53, 'uniquely_matched_scale_items': len(matched),
            'missing_scale_items': missing, 'ambiguous_scale_items': ambiguous,
            'unique_matched_positions': len({indices[key][0] for key in matched}),
            'outcome': 'pass' if len(matched) == 53 and len({indices[key][0] for key in matched}) == 53 else 'fail'})
    evidence = {'reporting_mode': 'presentation', 'executed_at': datetime.now(timezone.utc).isoformat(),
        'concept': 'Heartbeat relativo del V11', 'semantic_type': 'survey',
        'method': 'Inspección fresca de encabezados y correspondencia ordinal exacta con Q1–Q53; no se leen respuestas.',
        'acceptance_rule': 'Cada wave debe tener 53 posiciones ordinales únicas, una por ítem canónico.',
        'source_config': config_path.relative_to(ROOT).as_posix(), 'source_config_sha256': base.sha(config_path),
        'source_code': 'tools/audit_b_v11_heartbeat.py', 'source_code_sha256': base.sha(ROOT/'tools/audit_b_v11_heartbeat.py'),
        'dictionary': config['sources']['dictionary'], 'dictionary_sha256': metadata['dictionary_sha256'],
        'rows': rows, 'outcome': 'pass' if all(r['outcome']=='pass' for r in rows) else 'fail',
        'assessment_score_changed': False, 'employee_level_rows_read': False, 'employee_level_rows_persisted': False}
    base.write(target, evidence)
    print(json.dumps(evidence, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
