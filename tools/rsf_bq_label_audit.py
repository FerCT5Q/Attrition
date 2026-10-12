"""Recalculo agregado del contrato de etiquetas C frente al BQ archivado."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.codex/skills/attrition-redshift-db/scripts'))
import run_readonly_query as db
path = ROOT/'queries/audits/engineering_rsf_bq_label_contract_20261009.sql'
conn = db.connect()
conn.set_session(readonly=True,autocommit=True)
try:
    with conn.cursor() as cursor:
        cursor.execute(db.validate_readonly(path.read_text(encoding='utf-8')))
        columns = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
        if len(rows)!=1 or set(columns)!=set(['comparable_rows','matched_rows','common_positive_legacy_negative','common_negative_legacy_positive']):
            raise RuntimeError('Salida agregada fuera de contrato.')
        metrics = dict(zip(columns,map(int,rows[0])))
finally:
    conn.close()
okay = metrics=={'comparable_rows':238451,'matched_rows':238450,'common_positive_legacy_negative':1,'common_negative_legacy_positive':0}
evidence = {'reporting_mode':'presentation','date':datetime.now(timezone.utc).isoformat(),
    'query':str(path.relative_to(ROOT)),'sql_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'population':'Engineering; Employee; Regular; activo; sin RF360',
    'grain':'persona-foto, agregado global de siete snapshots; agosto 2025 a febrero 2026',
    'method':'Recalculo independiente de etiquetas con y sin limite de registro al 7-sep-2026.',
    'acceptance_rule':'238451 observaciones; una diferencia C=1/BQ=0 y ninguna inversa.',
    'metrics':metrics,'outcome':'pass' if okay else 'fail','score_changes':False}
output = ROOT/'output/analysis/engineering/20261008/random-survival-forest-v1/bq-label-contract-audit.json'
output.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(evidence,ensure_ascii=False))
if not okay:
    raise RuntimeError('Diferencias no explicadas por el contrato de registro.')
