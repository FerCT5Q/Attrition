"""Prueba temporal con personas ficticias y eventos conocidos con retraso."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'queries/profiles/engineering_b_v11_manager_history_person_month_20261011_v2.sql'
query=ROOT/'queries/audits/engineering_b_v11_manager_synthetic_20261011.sql'
path=ROOT/'config/b_playbook_v11_contracts/manager-synthetic.json'
if query.exists() or path.exists():
    raise RuntimeError('El fixture ya existe.')
months=[f"SELECT DATEADD(month,{m},DATE '2022-04-23')::DATE AS d" for m in range(26)]
people=[f'SELECT {i}::BIGINT AS pid' for i in range(1,91)]
events=[(1,'2024-02-05','2024-04-23'),(2,'2024-03-03','2024-05-23'),
        (31,'2024-02-05','2024-02-23'),(32,'2024-02-06','2024-02-23'),
        (90,'2022-09-15','2022-10-23')]
fixture='/* Fixture enteramente sintético; no contiene empleados reales. */\nWITH f_months AS ('+' UNION ALL '.join(months)+'),\n'
fixture+='f_people AS ('+' UNION ALL '.join(people)+'),\n'
fixture+='f_events AS ('+' UNION ALL '.join(f"SELECT {i}::BIGINT AS pid,DATE '{event}' AS event_date,DATE '{known}' AS known_date" for i,event,known in events)+'),\n'
fixture+='''fixture AS (
 SELECT m.d AS fis_mo_end_dt,p.pid AS employee_id,(1000+FLOOR((p.pid-1)/30.0))::BIGINT AS manager_employee_id,
 'test-region'::VARCHAR AS region,'test-family'::VARCHAR AS job_family,'L4'::VARCHAR AS job_level_primary_position,
 DATE '2020-01-01' AS max_hire_rehire_date,DATE '2020-01-01' AS service_date,DATE '2020-01-01' AS original_hire_date,
 'Engineering'::VARCHAR AS eng_or_noneng,'Employee'::VARCHAR AS worker_type,'Regular'::VARCHAR AS employee_type,
 CASE WHEN e.event_date IS NULL OR m.d<e.event_date THEN 1 ELSE 0 END AS active_status,0 AS is_rf360_yes_no,
 CASE WHEN m.d>=e.known_date THEN e.event_date END AS term_date,
 CASE WHEN m.d>=e.known_date THEN 'Voluntary'::VARCHAR END AS term_type
 FROM f_months m CROSS JOIN f_people p LEFT JOIN f_events e ON e.pid=p.pid
),
'''
body=source.read_text(encoding='utf-8').split('-- MODEL_OUTPUT')[0].split('WITH dates AS (',1)[1]
body='dates AS ('+body.replace('hrda.post_hire_monthly_worker_dtls','fixture')
body=body.replace('__PERIOD_START__','2024-04-23').replace('__PERIOD_END__','2024-05-23')
query.write_text(fixture+body+'''
SELECT COUNT(*) AS synthetic_cases,
 SUM(CASE WHEN employee_id<=30 AND snapshot_date=DATE '2024-04-23' AND manager_team_exits6_v11<>'1' THEN 1
          WHEN employee_id<=30 AND snapshot_date=DATE '2024-05-23' AND manager_team_exits6_v11<>'2+' THEN 1 ELSE 0 END) AS delayed_knowledge_mismatches,
 SUM(CASE WHEN latest_known_date>snapshot_date THEN 1 ELSE 0 END) AS future_event_violations,
 SUM(CASE WHEN employee_id<=30 AND snapshot_date=DATE '2024-04-23' AND manager_above_average18<>'(historia no confirmada)' THEN 1
          WHEN employee_id<=30 AND snapshot_date=DATE '2024-05-23' AND manager_above_average18='(historia no confirmada)' THEN 1 ELSE 0 END) AS eighteen_interval_mismatches
FROM encoded;
''',encoding='utf-8')
contract={'schema_version':4,'id':'manager-synthetic','title':'Prueba sintética de conocimiento tardío de salidas',
 'claim':'Una salida efectiva en marzo, registrada en mayo, no entra en la señal de abril; sí entra en mayo.',
 'use':'Comprobar la frontera temporal y el mínimo de dos salidas de la ventana de 18 intervalos.',
 'semantic_type':'derived_feature','population':'Noventa personas ficticias en tres equipos; ningún dato HR real',
 'grain':'persona ficticia-foto','known_at':'La fecha de conocimiento está definida expresamente en cada evento del fixture',
 'window':'Veintiséis fotos ficticias; dos fechas objetivo','history':'Se recrea una secuencia con salidas informadas con retraso.',
 'query':query.relative_to(ROOT).as_posix(),'zero_fields':['delayed_knowledge_mismatches','future_event_violations','eighteen_interval_mismatches'],
 'positive_fields':['synthetic_cases'],'expected_rows':1,
 'acceptance_rule':'Cero diferencias frente a los conteos esperados por las fechas explícitas de los eventos.',
 'conclusion_if_pass':'La implementación respeta la fecha de conocimiento en los casos de prueba',
 'limitation':'El fixture no sustituye la reconciliación histórica agregada.',
 'action':'Conservar la evidencia junto con las auditorías de seis y dieciocho intervalos'}
path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Fixture temporal de manager preparado; sin datos reales.')
