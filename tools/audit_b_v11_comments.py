"""Valida fuentes locales, clasificación y enlace anual; conserva sólo agregados."""
from datetime import datetime,timezone
import secrets

import b_incremental_data as data
import b_v11_qvoice_comments as comments
import engineering_model_c as base
from qvoice_model_data import load_config

ROOT=base.ROOT
OUT=ROOT/'output/analysis/engineering/20261011/b-playbook-v11-v1'
target=OUT/'input-evidence/v11-qvoice-comments.json'
if target.exists():
    raise RuntimeError('Ya existe la evidencia.')
contract_path=ROOT/'config/b_playbook_v11_contracts/qvoice-comments.json'
contract=base.read(contract_path)
for path,digest in contract['source_hashes'].items():
    if base.sha(ROOT/path)!=digest:
        raise RuntimeError('Cambió la taxonomía congelada.')
config=base.read(ROOT/'config/engineering_b_incremental_20261011_v2.json')
config['training_start']='2025-01-01'
data.check_authorization(config)
salt=secrets.token_hex(32)
frame=data.read_frame(contract['query'],{'snapshot_date','person_key','source_rows','same_episode_2024','same_episode_2025'},
    [],config,salt,'Enlace QVoice V11')
if not frame.source_rows.eq(1).all():
    raise RuntimeError('La población fuente tiene duplicados.')
qconfig=load_config(ROOT/config['source_qvoice_config'])
metadata=base.read(ROOT/config['source_qvoice_metadata'])
result,evidence=comments.attach(frame,qconfig,metadata,salt,verify=True)
population=[]
independent=base.read(OUT/'input-evidence/job-family.json')['rows']
for year,part in result.groupby(result.snapshot_date.dt.year,observed=True):
    row=next(r for r in independent if r['year']==year)
    if len(part)!=row['person_snapshots'] or part.person_key.nunique()!=row['employee_count']:
        raise RuntimeError('La población no reconcilia con el agregado independiente.')
    population.append({'year':int(year),'person_snapshots':len(part),'employee_count':int(part.person_key.nunique())})
evidence.update(executed_at=datetime.now(timezone.utc).isoformat(),query=contract['query'],
    sql_sha256=base.sha(ROOT/contract['query']),contract_path=contract_path.relative_to(ROOT).as_posix(),
    contract_sha256=base.sha(contract_path),transformer_source='tools/b_v11_qvoice_comments.py',
    transformer_sha256=base.sha(ROOT/'tools/b_v11_qvoice_comments.py'),source_hashes=contract['source_hashes'],
    population=population,rows=data.feature_support(result,comments.FEATURES),
    acceptance_rule=contract['acceptance_rule'],limitation=contract['limitation'])
base.write(target,evidence)
print({'outcome':'pass','features':len(comments.FEATURES),'sources':evidence['sources'],'population':population},flush=True)
