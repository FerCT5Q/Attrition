"""Contrato explícito del V11; sólo metadata y reglas antes de leer comentarios."""
import json
from pathlib import Path
from datetime import datetime,timezone

import b_v11_qvoice_comments as comments
import engineering_model_c as base
from qvoice_model_data import load_config

ROOT=base.ROOT
target=ROOT/'config/b_playbook_v11_contracts/qvoice-comments.json'
if target.exists():
    raise RuntimeError('El contrato ya existe.')
qconfig=load_config(ROOT/'config/qvoice_model_calibrated_20261008.yaml')
metadata=base.read(ROOT/'output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/preflight/source-metadata.json')
waves=[]
for wave in qconfig['sources']['waves']:
    if wave['year'] not in {2024,2025}:
        continue
    meta=next(m for m in metadata['waves'] if m['year']==wave['year'])
    _,_,roles,_=comments.mapping_for(wave,meta)
    waves.append({'year':wave['year'],'model_year':wave['year']+1,'source':wave['file'],
        'sha256':meta['sha256'],'prompt_roles':list(roles),'prompt_headers':roles})
paths=['tools/b_v11_qvoice_comments.py','tools/build_qvoice_comment_evidence.py',
    'tools/build_qvoice_retention_concerns_evidence.py','tools/build_qvoice_open_text_request_concern_evidence.py']
contract={'schema_version':4,'id':'qvoice-comments','reporting_mode':'presentation',
    'created_at':datetime.now(timezone.utc).isoformat(),'semantic_type':'survey',
    'claim':'Indicadores de mención/presencia del V11, con taxonomía congelada y desfase anual.',
    'population':'Employee, Regular, Engineering, activo y sin RF360','grain':'persona-foto con enlace participante-wave',
    'query':'queries/profiles/engineering_b_v11_qvoice_link_person_month_20261011.sql',
    'acceptance_rule':'Cero diferencias frente a helpers originales en muestra determinista de al menos 30 registros por wave; población anual reconciliada, sin duplicados usados ni waves futuras.',
    'sources':waves,'features':comments.FEATURES,'feature_labels':comments.LABELS,
    'source_hashes':{p:base.sha(ROOT/p) for p in paths},
    'header_reconciliation':{'path':'output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence/v11-qvoice-comment-keys.json',
        'sha256':base.sha(ROOT/'output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence/v11-qvoice-comment-keys.json')},
    'temporal_policy':'config/qvoice_annual_lag_policy_20261008.json',
    'limitation':'Los temas no equivalen a sentimiento o intención. El prompt de procesos sólo existe desde 2025; no se usan los temas más frecuentes de 2026 para seleccionar.',
    'employee_level_rows_persisted':False,'comment_text_persisted':False,'assessment_score_changed':False}
target.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print({'features':len(comments.FEATURES),'waves':[w['year'] for w in waves],'outcome':'contract_prepared'})
