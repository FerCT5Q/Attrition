"""Diagnóstico acotado del proxy de ciudad, sin conservar componentes individuales."""
from collections import defaultdict
from datetime import datetime,timezone
import secrets

import b_incremental_data as data
from b_v11_commute import CommuteTransform
import engineering_model_c as base

ROOT=base.ROOT
OUT=ROOT/'output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence'
target=OUT/'v11-commute-mapping.json'
if target.exists():
    raise RuntimeError('Ya existe la evidencia.')
metadata_path=ROOT/'queries/audits/engineering_b_v11_commute_metadata_followup_20261011.sql'
with base.db.connect() as connection:
    connection.set_session(readonly=True,autocommit=True)
    with connection.cursor() as cursor:
        cursor.execute(base.db.validate_readonly(metadata_path.read_text(encoding='utf-8')))
        names=[c[0] for c in cursor.description]
        metadata=[dict(zip(names,row)) for row in cursor.fetchmany(100)]


class Diagnostic(CommuteTransform):
    def __init__(self):
        super().__init__()
        self.country_totals=defaultdict(lambda:defaultdict(int))

    def __call__(self,frame):
        result=super().__call__(frame)
        cols=frame[self.input_columns].fillna('')
        for row in cols.itertuples(index=False,name=None):
            record=dict(zip(self.input_columns,row))
            if record['onsite_flag']!=1:
                continue
            counts=self.country_totals[record['country_label'] or 'Sin país laboral']
            counts['onsite_people']+=1
            value=self.cache.get(row)
            if value and not value[0].startswith('('):
                counts['calculable_people']+=1
                counts['ambiguous_office_people']+=int(value[1])
                counts['office_fallback_people']+=int(value[2])
                counts['over500_km_people']+=int(value[3])
        return result


config=base.read(ROOT/'config/engineering_b_incremental_20261011_v2.json')
config.update(training_start='2026-08-23',knowledge_boundary='2026-08-23')
data.check_authorization(config)
transform=Diagnostic()
query='queries/profiles/engineering_b_v11_commute_inputs_20261011.sql'
frame=data.read_frame(query,{'snapshot_date','person_key',*transform.input_columns},transform.features,
    config,secrets.token_hex(32),'Diagnóstico de distancia agosto 2026',transform)
rows=[]
for country,metrics in sorted(transform.country_totals.items()):
    if metrics['onsite_people']<30:
        continue
    rows.append({'country':country,**{key:(None if 0<value<30 else value) for key,value in metrics.items()}})
result={'reporting_mode':'presentation','executed_at':datetime.now(timezone.utc).isoformat(),
    'query':query,'sql_sha256':base.sha(ROOT/query),'snapshot':'2026-08-23',
    'metadata_query':metadata_path.relative_to(ROOT).as_posix(),'metadata_sha256':base.sha(metadata_path),
    'metadata':metadata,'rows':rows,'outcome':'pass_for_city_proxy_only',
    'acceptance_rule':'Reconciliar población; conservar desconocidos y no llamar traslado real al proxy por ciudad.',
    'no_structured_home_country':not any(r['column_name'] in ['home_country','home_country_code'] for r in metadata),
    'employee_level_rows_persisted':False,'location_hashes_persisted':False,'assessment_score_changed':False}
base.write(target,result)
print({'outcome':result['outcome'],'no_structured_home_country':result['no_structured_home_country'],'rows':rows},flush=True)
