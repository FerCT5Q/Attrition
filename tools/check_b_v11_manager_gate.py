"""Prueba enfocada del filtro temporal real, con eventos enteramente ficticios."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'queries/profiles/engineering_b_v11_manager_history_person_month_20261011_v2.sql').read_text(encoding='utf-8')
query=ROOT/'queries/audits/engineering_b_v11_manager_gate_synthetic_20261011.sql'
path=ROOT/'config/b_playbook_v11_contracts/manager-gate-synthetic.json'
if query.exists() or path.exists():
    raise RuntimeError('El fixture enfocado ya existe.')
events=[(1,98,10,'2024-02-05','2024-04-23',None),
        (2,99,10,'2024-03-03','2024-05-23',None),
        (3,98,20,'2024-02-05','2024-04-23','2024-04-23'),
        (4,98,30,'2024-02-05','2024-04-23','2024-05-23'),
        (5,102,40,'2024-06-01','2024-04-23',None),
        (6,75,50,'2022-03-03','2024-04-23',None)]
rows=[]
for person,seq,manager,effective,known,conflict in events:
    end='NULL::DATE' if conflict is None else f"DATE '{conflict}'"
    rows.append(f"SELECT {person} AS employee_id,{seq} AS seq,{manager} AS manager_id,'fixture'::VARCHAR AS stratum,DATE '{effective}' AS term_date,DATE '{known}' AS known_date,{end} AS conflicting_known_date")
known='known_events AS ('+source.split('known_events AS (',1)[1].split('), team_intervals AS (',1)[0]+')'
observed='observed AS ('+source.split('observed AS (',1)[1].split('), stratum_events AS (',1)[0]+')'
expected=[]
for date,seq in [('2024-04-23',100),('2024-05-23',101)]:
    for manager in [10,20,30,40,50]:
        # Oráculo: fechas y condiciones explícitas de los fixtures; no SQL.
        count=sum(m==manager and 0<seq-s<=6 and k<=date and (c is None or c>date)
                  for _,s,m,e,k,c in events)
        expected.append(f"SELECT DATE '{date}' AS snapshot_date,{manager} AS manager_id,{count} AS expected_count")
sql="""/* Sólo eventos sintéticos. Se prueba el filtro del SQL real. */
WITH targets AS (
 SELECT DATE '2024-04-23' AS snapshot_date,100 AS seq
 UNION ALL SELECT DATE '2024-05-23',101
), attributions AS (
"""+'\nUNION ALL\n'.join(rows)+'\n),\n'+known+',\n'+observed+',\nexpected AS (\n'+'\nUNION ALL\n'.join(expected)+'''
)
SELECT COUNT(*) AS synthetic_cases,
 SUM(CASE WHEN COALESCE(o.exits6,0)<>e.expected_count THEN 1 ELSE 0 END) AS knowledge_window_mismatches,
 SUM(CASE WHEN o.latest_known_date>e.snapshot_date THEN 1 ELSE 0 END) AS future_event_violations
FROM expected e LEFT JOIN observed o ON o.snapshot_date=e.snapshot_date AND o.manager_id=e.manager_id;
'''
query.write_text(sql,encoding='utf-8')
contract={'schema_version':4,'id':'manager-gate-synthetic','title':'Casos sintéticos de conocimiento y ventana de eventos',
 'claim':'El filtro excluye eventos aún no conocidos, conflictos de tipo ya conocidos e intervalos futuros o fuera de ventana.',
 'use':'Verificar el filtro temporal exacto usado por las señales del manager.',
 'semantic_type':'derived_feature','population':'Eventos y managers ficticios; ninguna fila HR',
 'grain':'equipo ficticio-fecha','known_at':'Fechas explícitas de conocimiento, conflicto e intervalo en cada fixture',
 'window':'Dos fechas ficticias y cinco escenarios','history':'Prueba enfocada, independiente de los agregados históricos.',
 'query':query.relative_to(ROOT).as_posix(),'zero_fields':['knowledge_window_mismatches','future_event_violations'],
 'positive_fields':['synthetic_cases'],'expected_rows':1,
 'acceptance_rule':'Cero diferencias entre el SQL real y el conteo independiente por fechas explícitas.',
 'conclusion_if_pass':'El filtro temporal se comporta como se definió en los casos probados',
 'limitation':'No sustituye las auditorías de exposición, suavizado y benchmark sobre el histórico completo.',
 'action':'Conservar los dos tipos de evidencia'}
path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Diez casos enfocados preparados.')
