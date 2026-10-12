"""Reconciliación de features geográficas, conservando únicamente agregados."""
from datetime import datetime,timezone
import argparse
import secrets
import sys
from pathlib import Path

import b_incremental_data as data
from b_v11_geography import transformer_for
import engineering_model_c as base

ROOT=base.ROOT
OUT=ROOT/'output/analysis/engineering/20261011/b-playbook-v11-v1'


def run(kind):
    config=base.read(ROOT/'config/engineering_b_incremental_20261011_v2.json')
    data.check_authorization(config)
    transformer=transformer_for(kind+'_v11')
    audit_id='timezone-v3' if kind=='timezone' else 'commute-inputs'
    contract_path=ROOT/f'config/b_playbook_v11_contracts/{audit_id}.json'
    contract=base.read(contract_path)
    target=OUT/f'input-evidence/v11-{kind}-prepared.json'
    if target.exists():
        raise RuntimeError('La evidencia ya existe.')
    component_evidence=base.read(OUT/f'input-evidence/v11-{audit_id}.json')
    if component_evidence['outcome']!='pass':
        raise RuntimeError('Los componentes no están validados.')
    frame=data.read_frame(contract['source_query'],{'snapshot_date','person_key',*transformer.input_columns},
        transformer.features,config,secrets.token_hex(32),kind,transformer)
    evidence=transformer.evidence()
    for row in evidence['rows']:
        independent=next(r for r in component_evidence['rows'] if r['year']==row['year'])
        fields=['person_snapshots','employee_count']+(['colocation_observable','same_site_city_rows'] if kind=='timezone' else [])
        if any(row[field]!=independent[field] for field in fields):
            raise RuntimeError('No reconcilia la transformación geográfica con el agregado independiente.')
    transformer_path=Path(sys.modules[type(transformer).__module__].__file__).resolve()
    evidence.update(executed_at=datetime.now(timezone.utc).isoformat(),query=contract['source_query'],
        sql_sha256=base.sha(ROOT/contract['source_query']),contract_path=contract_path.relative_to(ROOT).as_posix(),
        contract_sha256=base.sha(contract_path),source_audit=component_evidence['query'],
        transformer_source=transformer_path.relative_to(ROOT).as_posix(),transformer_sha256=base.sha(transformer_path),
        total_rows=len(frame),duplicate_output_keys=int(frame.duplicated(['snapshot_date','person_key']).sum()),
        output_columns=list(frame.columns))
    if evidence['duplicate_output_keys']:
        raise RuntimeError('Grain de salida duplicado.')
    base.write(target,evidence)
    print({'concept':kind,'outcome':'pass','annual':evidence['rows']},flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind',choices=['timezone','commute'])
    run(parser.parse_args().kind)
