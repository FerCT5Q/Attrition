"""Reconciliación de llaves repetidas de encabezado; sólo conteos fuera de RAM."""
from datetime import datetime,timezone

import engineering_model_c as base
from qvoice_model_data import iter_structured_rows,parse_key

ROOT=base.ROOT
OUT=ROOT/'output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence/v11-qvoice-comment-keys.json'
if OUT.exists():
    raise RuntimeError('La evidencia ya existe.')
metadata=base.read(ROOT/'output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/preflight/source-metadata.json')
wave=next(m for m in metadata['waves'] if m['year']==2024)
if base.sha(ROOT/wave['file'])!=wave['sha256']:
    raise RuntimeError('Cambió el archivo de 2024.')
headers=list(wave['headers'])
positions=[i for i,h in enumerate(headers) if h=="Participant's Unique Identifier"]
if positions!=[1,249]:
    raise RuntimeError('Cambió la ambigüedad a verificar.')
headers[positions[0]]='primary_key_for_audit'
headers[positions[1]]='repeated_key_for_audit'
required={headers[p] for p in positions}
counts=dict(source_rows=0,comparable_rows=0,matched_rows=0,mismatched_rows=0,primary_missing_rows=0,repeated_missing_rows=0)
for indexes,row in iter_structured_rows(ROOT/wave['file'],'Raw data',headers,required):
    a=parse_key(row.get(indexes['primary_key_for_audit']))
    b=parse_key(row.get(indexes['repeated_key_for_audit']))
    counts['source_rows']+=1
    counts['primary_missing_rows']+=int(a is None)
    counts['repeated_missing_rows']+=int(b is None)
    if a is not None and b is not None:
        counts['comparable_rows']+=1
        counts['matched_rows']+=int(a==b)
        counts['mismatched_rows']+=int(a!=b)
outcome='pass' if counts['mismatched_rows']==0 and counts['comparable_rows']>=30 else 'fail'
base.write(OUT,{'reporting_mode':'presentation','executed_at':datetime.now(timezone.utc).isoformat(),
    'source':wave['file'],'source_sha256':wave['sha256'],'year':2024,'positions_zero_based':positions,
    'selected_position_zero_based':1,'acceptance_rule':'Al menos 30 pares comparables y cero contradicciones; conservar el bloque original, sin completar con la segunda llave.',
    'rows':[counts],'outcome':outcome,'employee_level_rows_persisted':False,'identifiers_persisted':False})
print({'outcome':outcome,**counts},flush=True)
if outcome!='pass':
    raise RuntimeError('No se confirmó equivalencia de la llave repetida.')
