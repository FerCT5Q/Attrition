"""Congela el contrato y el agregado independiente de componentes de distancia."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
model=ROOT/'queries/profiles/engineering_b_v11_commute_inputs_20261011.sql'
audit=ROOT/'queries/audits/engineering_b_v11_commute_inputs_20261011.sql'
contract=ROOT/'config/b_playbook_v11_contracts/commute-inputs.json'
if audit.exists() or contract.exists():
    raise RuntimeError('Ya existe esta preparación.')
prefix=model.read_text(encoding='utf-8').split('-- MODEL_OUTPUT')[0]
audit.write_text((prefix+'''
SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
       COUNT(*) AS person_snapshots,COUNT(DISTINCT employee_id) AS employee_count,
       SUM(CASE WHEN source_rows>1 THEN 1 ELSE 0 END) AS duplicate_source_keys,
       SUM(CASE WHEN valid_components<>1 THEN 1 ELSE 0 END) AS conflicting_input_rows,
       SUM(CASE WHEN onsite_flag=1 THEN 1 ELSE 0 END) AS onsite_rows,
       SUM(CASE WHEN onsite_flag=-1 THEN 1 ELSE 0 END) AS arrangement_unknown_rows,
       SUM(CASE WHEN country_label IS NOT NULL AND city_label IS NOT NULL
                      AND office_hash IS NOT NULL AND postal_hash IS NOT NULL AND valid_components=1
                THEN 1 ELSE 0 END) AS complete_location_rows,
       SUM(CASE WHEN onsite_flag=1 AND country_label IS NOT NULL AND city_label IS NOT NULL
                      AND office_hash IS NOT NULL AND postal_hash IS NOT NULL AND valid_components=1
                THEN 1 ELSE 0 END) AS complete_onsite_rows
FROM encoded GROUP BY 1 ORDER BY 1
''').replace('__PERIOD_START__','2020-07-26').replace('__PERIOD_END__','2026-09-07'),encoding='utf-8')
c=dict(schema_version=4,id='commute-inputs',title='Componentes históricos de la distancia estimada',
    claim='La modalidad y ubicación pertenecen a la foto y no tienen duplicados o contradicciones.',
    use='Probar la distancia del V11 sobre B, usando sólo bandas.',semantic_type='external_source',
    population='Employee, Regular, activo, Engineering, sin RF360',grain='persona-foto',
    known_at='Ubicación y modalidad en t; catálogos estáticos de 2026 sin vigencia histórica demostrada.',
    window='2020-07-26 a 2026-09-07',history='La preparación descriptiva V11 se adapta a la historia mensual; oficinas ambiguas producen un proxy mínimo declarado.',
    query=audit.relative_to(ROOT).as_posix(),source_query=model.relative_to(ROOT).as_posix(),
    zero_fields=['duplicate_source_keys','conflicting_input_rows'],positive_fields=['person_snapshots','onsite_rows','complete_onsite_rows'],expected_rows=7,
    acceptance_rule='Cero duplicados y conflictos de componentes; recálculo geográfico posterior con diferencia máxima de 0.0001 km y población anual reconciliada.',
    conclusion_if_pass='Componentes habilitados para la reconciliación en RAM',
    limitation='No acredita residencia histórica exacta, traslado real ni vigencia histórica del catálogo externo.',
    action='Transformar hashes en bandas sólo en RAM, conservar desconocidos y documentar cobertura')
contract.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Distancia: contrato de componentes y consulta agregada congelados.')
