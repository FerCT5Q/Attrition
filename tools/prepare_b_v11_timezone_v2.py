"""Sustituye CASE por joins de catálogos públicos pequeños; misma definición."""
import json
from pathlib import Path
import build_v7_manager_timezone_annual_attrition_evidence as geo

ROOT=geo.ROOT
sites,cities,_=geo.zone_maps()


def map_cte(name,values):
    return name+' AS (\n'+'\nUNION ALL\n'.join(
        f"SELECT '{key}'::VARCHAR(32) AS map_key,'{zone}'::VARCHAR(64) AS zone_name"
        for key,zone in sorted(values.items()))+'\n)'


for kind in ['profiles','audits']:
    stem='engineering_b_v11_timezone_person_month_20261011' if kind=='profiles' else 'engineering_b_v11_timezone_20261011'
    old=ROOT/f'queries/{kind}/{stem}.sql'
    target=old.with_stem(stem+'_v2')
    if target.exists():
        raise RuntimeError('La revisión ya existe.')
    sql=old.read_text(encoding='utf-8')
    start=sql.index('), zones AS (')
    end=sql.index('), mapped AS (',start)
    sql=sql[:start]+'), '+map_cte('site_map',sites)+', '+map_cte('city_map',cities)+''', zones AS (
 SELECT w.snapshot_date,w.employee_id,w.manager_id,w.engineering,w.site_key,w.city_key,w.source_rows,w.manager_variants,w.site_variants,w.city_variants,
        s.zone_name AS site_zone,c.zone_name AS city_zone
 FROM workforce w
 LEFT JOIN site_map s ON s.map_key=w.site_key
 LEFT JOIN city_map c ON c.map_key=w.city_key
'''+sql[end:]
    target.write_text(sql,encoding='utf-8')
contract_path=ROOT/'config/b_playbook_v11_contracts/timezone.json'
c=json.loads(contract_path.read_text(encoding='utf-8'))
c.update(id='timezone-v2',query='queries/audits/engineering_b_v11_timezone_20261011_v2.sql',source_query='queries/profiles/engineering_b_v11_timezone_person_month_20261011_v2.sql')
c['history']+=' Revisión computacional: joins contra mapas públicos únicos en vez de repetir CASE por persona; la primera consulta se canceló por coste y no aporta evidencia.'
(contract_path.parent/'timezone-v2.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Timezone v2: preparado mediante dos mapas de claves públicas unívocas.')
