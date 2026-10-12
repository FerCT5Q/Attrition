"""Comprueba contratos, fuentes y alcance antes de cargar las filas en RAM."""
from datetime import datetime, timezone

import engineering_b_incremental as inc
import engineering_model_c as base
import b_incremental_data as data


def main():
    path = inc.DEFAULT
    config = base.read(path)
    out = base.ROOT/config['output']
    data.check_authorization(config)
    ledger = data.input_ledger(config,out)
    for name in ['base_query','history_query','pending_query']:
        base.db.validate_readonly((base.ROOT/config[name]).read_text(encoding='utf-8'))
    for block in config['extra_hr_queries']:
        base.db.validate_readonly((base.ROOT/block['query']).read_text(encoding='utf-8'))
    for source in config['additional_reproducibility_sources']:
        if not (base.ROOT/source).is_file():
            raise RuntimeError('Falta fuente congelable: '+source)
    source = base.read(base.ROOT/config['qvoice_comments_contract'])
    for item,digest in source['source_hashes'].items():
        if base.sha(base.ROOT/item)!=digest:
            raise RuntimeError('Cambió preparación de comentarios: '+item)
    if base.sha(base.ROOT/source['header_reconciliation']['path'])!=source['header_reconciliation']['sha256']:
        raise RuntimeError('Cambió reconciliación de encabezados.')
    for kind in ['timezone','commute']:
        evidence = base.read(out/f'input-evidence/v11-{kind}-prepared.json')
        if base.sha(base.ROOT/evidence['catalog'])!=evidence['catalog_sha256']:
            raise RuntimeError('Cambió catálogo geográfico.')
        for item in evidence.get('centroid_sources',{}).values():
            if item.get('path') and base.sha(base.ROOT/item['path'])!=item['sha256']:
                raise RuntimeError('Cambió catálogo postal.')
    scope = base.read(base.ROOT/config['playbook_scope'])
    available = set(inc.hr_candidates(config)+inc.q_candidates(config))|set(inc.B_TERMS)
    if not set(f for r in scope['views'] for f in r['representaciones'])<=available:
        raise RuntimeError('El scope referencia una variable ausente.')
    result = {'outcome':'pass','executed_at':datetime.now(timezone.utc).isoformat(),
        'reporting_mode':'presentation','config':path.relative_to(base.ROOT).as_posix(),
        'config_sha256':base.sha(path), 'accepted_evidence_entries':len(ledger['entries']),
        'hr_candidates':len(inc.hr_candidates(config)), 'qvoice_candidates':len(inc.q_candidates(config)),
        'all_base_terms_preserved':True, 'queries_readonly':True,
        'employee_level_rows_read':False,'employee_level_rows_persisted':False,'training_started':False}
    base.write(out/'inputs-ready.json',result)
    print(result,flush=True)


if __name__=='__main__':
    main()
