"""Cuantifica la discrepancia numérica del recálculo del benchmark."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'queries/profiles/engineering_b_v11_manager_history_person_month_20261011_v2.sql'
query=ROOT/'queries/audits/engineering_b_v11_manager_benchmark_precision_20261011.sql'
path=ROOT/'config/b_playbook_v11_contracts/manager-benchmark-precision.json'
if query.exists() or path.exists():
    raise RuntimeError('La comprobación ya existe.')
prefix=source.read_text(encoding='utf-8').split('), encoded AS (')[0]+')\n'
prefix=prefix.replace('__PERIOD_START__','2026-08-23').replace('__PERIOD_END__','2026-08-23')
sql=prefix+'''SELECT v.snapshot_date,COUNT(*) AS eligible_managers,
 SUM(v.exposure18) AS exposure18,SUM(v.exits18) AS exits18,
 MAX(b.benchmark) AS benchmark,MAX(b.independent_benchmark) AS independent_decimal_weights,
 SUM(v.rate18*v.exposure18)/SUM(v.exposure18) AS independent_exposure_weights,
 SUM(v.rate18*(v.exposure18::DOUBLE PRECISION/18))/SUM(v.exposure18::DOUBLE PRECISION/18) AS independent_float_weights,
 MAX(ABS(v.exposure18/18.0-v.exposure18::DOUBLE PRECISION/18)) AS maximum_weight_rounding_difference
FROM values6 v JOIN benchmarks b ON b.snapshot_date=v.snapshot_date
WHERE v.eligible18=1 GROUP BY 1 HAVING COUNT(*)>=30;
'''
query.write_text(sql,encoding='utf-8')
contract={'schema_version':4,'id':'manager-benchmark-precision','title':'Reconciliación de precisión del benchmark de 18 intervalos',
 'claim':'¿La discrepancia proviene del redondeo de pesos decimales o de un error en el benchmark principal?',
 'use':'Resolver la auditoría fallida sin relajar la tolerancia arbitrariamente.',
 'semantic_type':'derived_feature','population':'Managers con historia elegible; resultados agregados, sin identidades',
 'grain':'foto agregada','known_at':'Historia conocida al 23-ago-2026','window':'Dieciocho intervalos previos al 23-ago-2026',
 'history':'La comparación de suma de eventos/exposición con promedio ponderado no cumplió la tolerancia de 1e-8.',
 'query':query.relative_to(ROOT).as_posix(),'zero_fields':[],'positive_fields':['eligible_managers'],'expected_rows':1,
 'acceptance_rule':'Medir las dos fórmulas independientes con pesos de exposición y pesos en doble precisión, además del redondeo de pesos original.',
 'conclusion_if_pass':'Se dispone de magnitudes para identificar la causa de la discrepancia',
 'limitation':'Este diagnóstico no habilita por sí solo el uso del indicador; debe cerrar la reconciliación.',
 'action':'Corregir la implementación que no conserve precisión y repetir la regla original'}
path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Diagnóstico de precisión del benchmark preparado.')
