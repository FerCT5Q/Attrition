"""Comprueba el inicio observado del feed antes de interpretar ceros."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'queries/profiles/engineering_b_v11_manager_history_person_month_20261011.sql'
query=ROOT/'queries/audits/engineering_b_v11_manager_feed_20261011.sql'
path=ROOT/'config/b_playbook_v11_contracts/manager-feed.json'
if query.exists() or path.exists():
    raise RuntimeError('La comprobación ya existe.')
sql=source.read_text(encoding='utf-8').split('), attributions AS (')[0]+')\n'
sql=sql.replace('__PERIOD_START__','2020-07-26').replace('__PERIOD_END__','2026-09-07')
sql+='''SELECT COUNT(*) AS event_keys,COUNT(DISTINCT employee_id) AS employee_count,
 MIN(known_date) AS first_known_voluntary_date,MAX(known_date) AS last_known_voluntary_date,
 MIN(CASE WHEN known_date IS NOT NULL THEN term_date END) AS first_effective_voluntary_date,
 SUM(CASE WHEN known_date<DATE '2022-01-01' THEN 1 ELSE 0 END) AS known_before_2022,
 SUM(CASE WHEN known_date IS NOT NULL AND known_date>DATEADD(day,45,term_date) THEN 1 ELSE 0 END) AS recorded_over_45_days_after_event,
 SUM(CASE WHEN known_date IS NOT NULL AND conflicting_known_date IS NOT NULL THEN 1 ELSE 0 END) AS conflicting_type_events
FROM event_sources HAVING COUNT(DISTINCT employee_id)>=30;
'''
query.write_text(sql,encoding='utf-8')
contract={'schema_version':4,'id':'manager-feed','title':'Inicio observado de salidas para contexto del manager',
 'claim':'¿El cero histórico representa un feed observado o un periodo anterior a su primera observación?',
 'use':'Evitar que falta de historia se convierta en cero salidas.', 'semantic_type':'derived_feature',
 'population':'Fuente de eventos usados para contexto agregado del manager; las asignaciones finales son Engineering',
 'grain':'evento deduplicado; resultado agregado global','known_at':'Primera foto con tipo Voluntary y fecha efectiva ya ocurrida',
 'window':'Contexto desde 2018-10-26 hasta 2026-09-07','history':'La auditoría previa encontró ausencia de O/E observable antes de 2022; se comprueba la causa antes de finalizar.',
 'query':query.relative_to(ROOT).as_posix(),'zero_fields':[],'positive_fields':['event_keys'],'expected_rows':1,
 'acceptance_rule':'Obtener fechas extremas y recuentos de historia tardía; el inicio observado se usará para codificar historia incompleta, sin asumir ceros.',
 'conclusion_if_pass':'Existe evidencia agregada para decidir el inicio admisible de las ventanas',
 'limitation':'Primera observación no acredita que un evento no existiera antes en otros sistemas.',
 'action':'Exigir una ventana completa posterior al inicio observado del feed'}
path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Comprobación de inicio del feed preparada.')
