"""Mueve el catálogo público a RAM; Redshift sólo enlaza fotos y devuelve hashes."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'queries/profiles/engineering_b_v11_timezone_person_month_20261011.sql'
prefix=old.read_text(encoding='utf-8').split('), zones AS (')[0]
prefix+='''), pairs AS (
 SELECT p.snapshot_date,p.employee_id,p.site_key,p.city_key,
        m.site_key AS manager_site,m.city_key AS manager_city,
        p.source_rows,m.source_rows AS manager_rows,m.employee_id AS matched_manager,
        m.snapshot_date AS manager_snapshot,
        CASE WHEN p.source_rows=1 AND p.manager_variants=1 AND p.site_variants=1
                       AND p.city_variants=1 AND m.source_rows=1
                       AND m.site_variants=1 AND m.city_variants=1
                       AND p.manager_id<>p.employee_id THEN 1 ELSE 0 END AS usable_pair
 FROM workforce p LEFT JOIN workforce m
   ON m.snapshot_date=p.snapshot_date AND m.employee_id=p.manager_id
 WHERE p.engineering='Engineering'
), encoded AS (
 SELECT snapshot_date,employee_id,site_key,city_key,manager_site,manager_city,
        source_rows,manager_rows,matched_manager,manager_snapshot,usable_pair,
        CASE WHEN usable_pair=1 AND site_key IS NOT NULL AND manager_site IS NOT NULL
                  AND city_key IS NOT NULL AND manager_city IS NOT NULL
             THEN CASE WHEN site_key=manager_site AND city_key=manager_city THEN 1 ELSE 0 END
             ELSE -1 END AS colocation_check
 FROM pairs
)
'''
model=ROOT/'queries/profiles/engineering_b_v11_timezone_person_month_20261011_v3.sql'
audit=ROOT/'queries/audits/engineering_b_v11_timezone_20261011_v3.sql'
if model.exists():
    raise RuntimeError('La preparación ya existe.')
model.write_text(prefix+'''-- MODEL_OUTPUT
SELECT snapshot_date,MD5(CAST(employee_id AS VARCHAR)||'__RUN_SALT__') AS person_key,
       site_key,city_key,manager_site,manager_city,usable_pair,colocation_check
FROM encoded
''',encoding='utf-8')
audit.write_text((prefix+'''
, site_history AS (
 SELECT site_key,COUNT(DISTINCT city_key) AS historical_cities
 FROM workforce WHERE site_key IS NOT NULL GROUP BY 1
)
SELECT EXTRACT(year FROM e.snapshot_date)::INTEGER AS year,
       COUNT(*) AS person_snapshots,COUNT(DISTINCT employee_id) AS employee_count,
       SUM(CASE WHEN source_rows>1 THEN 1 ELSE 0 END) AS duplicate_source_keys,
       SUM(CASE WHEN manager_rows>1 THEN 1 ELSE 0 END) AS multiple_manager_matches,
       SUM(CASE WHEN manager_snapshot<>e.snapshot_date THEN 1 ELSE 0 END) AS wrong_snapshot_matches,
       SUM(CASE WHEN matched_manager IS NOT NULL THEN 1 ELSE 0 END) AS manager_matches,
       SUM(CASE WHEN matched_manager IS NULL THEN 1 ELSE 0 END) AS manager_unmatched,
       SUM(usable_pair) AS valid_pairs,
       SUM(CASE WHEN colocation_check>=0 THEN 1 ELSE 0 END) AS colocation_observable,
       SUM(CASE WHEN colocation_check=1 THEN 1 ELSE 0 END) AS same_site_city_rows,
       SUM(CASE WHEN historical_cities>1 THEN 1 ELSE 0 END) AS rows_site_multiple_historical_cities
FROM encoded e LEFT JOIN site_history h ON h.site_key=e.site_key
GROUP BY 1 ORDER BY 1
''').replace('__PERIOD_START__','2020-07-26').replace('__PERIOD_END__','2026-09-07'),encoding='utf-8')
c=json.loads((ROOT/'config/b_playbook_v11_contracts/timezone.json').read_text(encoding='utf-8'))
c.update(id='timezone-v3',query=audit.relative_to(ROOT).as_posix(),source_query=model.relative_to(ROOT).as_posix(),
    zero_fields=['duplicate_source_keys','multiple_manager_matches','wrong_snapshot_matches'],
    positive_fields=['person_snapshots','colocation_observable','valid_pairs'])
c['history']+=' v1 y v2 se cancelaron por coste. v3 procesa el mapping público y offsets en RAM; la consulta valida la unión y se complementa con la reconciliación de la transformación y el control DST de 1036 casos.'
c['acceptance_rule']='Cero duplicados o uniones fuera de la foto; reconciliación posterior de categorías en RAM, sin guardar hashes de ubicaciones asociados a personas.'
(ROOT/'config/b_playbook_v11_contracts/timezone-v3.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Timezone v3 preparado; sólo pares de la misma foto, sin catálogos expandidos en SQL.')
