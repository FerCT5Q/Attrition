"""Congela el proxy de zona horaria del V11 y sus controles agregados."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json

import build_v7_manager_timezone_annual_attrition_evidence as geo

ROOT = geo.ROOT


def main():
    sites, cities, diagnostics = geo.zone_maps()
    source_path = ROOT/'queries/profiles/engineering_b_v11_timezone_person_month_20261011.sql'
    audit_path = ROOT/'queries/audits/engineering_b_v11_timezone_20261011.sql'
    contract_path = ROOT/'config/b_playbook_v11_contracts/timezone.json'
    if source_path.exists() or contract_path.exists():
        raise RuntimeError('La preparación ya existe; usar una revisión nueva.')
    # Reproduce la normalización del V11. El contrato no interpreta un código
    # idéntico como presencia física ni le asigna una dirección histórica.
    def norm(column):
        return f"NULLIF(REGEXP_REPLACE(UPPER(TRIM({column})), '[^A-Z0-9]+', ''),'')"
    site = norm('office_site')
    city = f"{norm('country')}||'|'||{norm('city')}"
    prefix = f"""/* Proxy geográfico estático del V11; modelo sólo en RAM.
   Oficinas públicas 2026; ubicación laboral de la propia foto, sin domicilios. */
WITH source AS (
 SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id,
        manager_employee_id, TRIM(eng_or_noneng) AS engineering,
        MD5({site}) AS site_key, MD5({city}) AS city_key
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '__PERIOD_START__' AND DATE '__PERIOD_END__'
   AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
   AND is_rf360_yes_no=0 AND employee_id IS NOT NULL
), workforce AS (
 SELECT snapshot_date,employee_id,MAX(manager_employee_id) AS manager_id,
        MAX(engineering) AS engineering, MAX(site_key) AS site_key, MAX(city_key) AS city_key,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(CAST(manager_employee_id AS VARCHAR),'<NULL>')) AS manager_variants,
        COUNT(DISTINCT COALESCE(site_key,'<NULL>')) AS site_variants,
        COUNT(DISTINCT COALESCE(city_key,'<NULL>')) AS city_variants
 FROM source GROUP BY 1,2
), zones AS (
 SELECT w.snapshot_date,w.employee_id,w.manager_id,w.engineering,w.site_key,w.city_key,w.source_rows,w.manager_variants,w.site_variants,w.city_variants,
        {geo.mapping_case('site_key', sites)} AS site_zone,
        {geo.mapping_case('city_key', cities)} AS city_zone
 FROM workforce w
), mapped AS (
 SELECT z.snapshot_date,z.employee_id,z.manager_id,z.engineering,z.site_key,z.city_key,z.source_rows,z.manager_variants,z.site_variants,z.city_variants,z.site_zone,z.city_zone, CASE WHEN site_zone IS NOT NULL AND city_zone IS NOT NULL
                       AND site_zone<>city_zone THEN NULL
                   ELSE COALESCE(site_zone,city_zone) END AS zone_name
 FROM zones z
), pairs AS (
 SELECT p.snapshot_date,p.employee_id,p.site_key,p.city_key,p.zone_name,
        m.snapshot_date AS manager_snapshot,m.employee_id AS matched_manager,
        m.site_key AS manager_site,m.city_key AS manager_city,m.zone_name AS manager_zone,
        p.source_rows,p.manager_variants,p.site_variants,p.city_variants,
        m.source_rows AS manager_rows,m.site_variants AS manager_site_variants,
        m.city_variants AS manager_city_variants,
        CASE WHEN p.site_zone IS NOT NULL AND p.city_zone IS NOT NULL
                       AND p.site_zone<>p.city_zone THEN 1 ELSE 0 END AS mapping_conflict,
        CASE WHEN p.source_rows=1 AND p.manager_variants=1 AND p.site_variants=1
                       AND p.city_variants=1 AND m.source_rows=1
                       AND m.site_variants=1 AND m.city_variants=1
                       AND p.manager_id<>p.employee_id THEN 1 ELSE 0 END AS usable_pair
 FROM mapped p LEFT JOIN mapped m
   ON m.snapshot_date=p.snapshot_date AND m.employee_id=p.manager_id
 WHERE p.engineering='Engineering'
), offsets AS (
 SELECT p.snapshot_date,p.employee_id,p.site_key,p.city_key,p.zone_name,p.manager_snapshot,p.matched_manager,p.manager_site,p.manager_city,p.manager_zone,p.source_rows,p.manager_variants,p.site_variants,p.city_variants,p.manager_rows,p.manager_site_variants,p.manager_city_variants,p.mapping_conflict,p.usable_pair,
   CONVERT_TIMEZONE('UTC',zone_name,DATEADD(hour,12,snapshot_date)) AS local_time,
   CONVERT_TIMEZONE('UTC',manager_zone,DATEADD(hour,12,snapshot_date)) AS manager_local_time
 FROM pairs p
), encoded AS (
 SELECT p.snapshot_date,p.employee_id,p.site_key,p.city_key,p.zone_name,p.manager_snapshot,p.matched_manager,p.manager_site,p.manager_city,p.manager_zone,p.source_rows,p.manager_variants,p.site_variants,p.city_variants,p.manager_rows,p.manager_site_variants,p.manager_city_variants,p.mapping_conflict,p.usable_pair,p.local_time,p.manager_local_time,
   CASE WHEN usable_pair<>1 OR site_key IS NULL OR manager_site IS NULL
                   OR city_key IS NULL OR manager_city IS NULL THEN '(unknown)'
        WHEN site_key=manager_site AND city_key=manager_city THEN 'same recorded site and city'
        ELSE 'different recorded site or city' END AS manager_colocation_v11,
   CASE WHEN usable_pair<>1 OR site_key IS NULL OR manager_site IS NULL THEN '(unknown)'
        WHEN site_key=manager_site THEN 'same recorded site'
        WHEN zone_name IS NULL OR manager_zone IS NULL THEN '(unmapped geography)'
        WHEN ABS(DATEDIFF(minute,local_time,manager_local_time))<=240 THEN 'different site up to 4 hours'
        ELSE 'different site more than 4 hours' END AS manager_timezone_relation
 FROM offsets p
)
"""
    output = """-- MODEL_OUTPUT
SELECT snapshot_date,MD5(CAST(employee_id AS VARCHAR)||'__RUN_SALT__') AS person_key,
       manager_colocation_v11,manager_timezone_relation
FROM encoded
"""
    source_path.write_text(prefix+output,encoding='utf-8')
    audit = """
, site_history AS (
 SELECT site_key,COUNT(DISTINCT city_key) AS cities,COUNT(DISTINCT city_zone) AS zones
 FROM zones WHERE site_key IS NOT NULL GROUP BY 1
), annual AS (
 SELECT EXTRACT(year FROM e.snapshot_date)::INTEGER AS year,
        COUNT(*) AS person_snapshots,COUNT(DISTINCT e.employee_id) AS employee_count,
        SUM(CASE WHEN e.source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_source_keys,
        SUM(CASE WHEN matched_manager IS NOT NULL THEN 1 ELSE 0 END) AS manager_matches,
        SUM(CASE WHEN matched_manager IS NULL THEN 1 ELSE 0 END) AS manager_unmatched,
        SUM(CASE WHEN manager_rows>1 THEN 1 ELSE 0 END) AS multiple_manager_matches,
        SUM(CASE WHEN manager_snapshot<>e.snapshot_date THEN 1 ELSE 0 END) AS wrong_snapshot_matches,
        SUM(mapping_conflict) AS mapping_conflict_rows,
        SUM(CASE WHEN h.cities>1 THEN 1 ELSE 0 END) AS rows_site_multiple_historical_cities,
        SUM(CASE WHEN h.zones>1 THEN 1 ELSE 0 END) AS rows_site_multiple_historical_zones,
        SUM(CASE WHEN manager_colocation_v11<>'(unknown)' THEN 1 ELSE 0 END) AS colocation_observable,
        SUM(CASE WHEN manager_timezone_relation NOT LIKE '(%' THEN 1 ELSE 0 END) AS timezone_observable,
        SUM(CASE WHEN manager_timezone_relation='same recorded site' THEN 1 ELSE 0 END) AS same_site_rows,
        SUM(CASE WHEN manager_timezone_relation='different site up to 4 hours' THEN 1 ELSE 0 END) AS up_to_four_hours_rows,
        SUM(CASE WHEN manager_timezone_relation='different site more than 4 hours' THEN 1 ELSE 0 END) AS over_four_hours_rows,
        SUM(CASE WHEN usable_pair<>1 AND (manager_colocation_v11<>'(unknown)'
                      OR manager_timezone_relation NOT LIKE '(%') THEN 1 ELSE 0 END) AS invalid_pair_used,
        SUM(CASE WHEN manager_timezone_relation LIKE 'different site%'
                  AND ((ABS(EXTRACT(epoch FROM local_time)-EXTRACT(epoch FROM manager_local_time))/60<=240)
                    <>(manager_timezone_relation='different site up to 4 hours'))
                 THEN 1 ELSE 0 END) AS independent_formula_mismatches,
        SUM(CASE WHEN manager_colocation_v11='same recorded site and city'
                   AND (e.site_key<>manager_site OR e.city_key<>manager_city) THEN 1 ELSE 0 END) AS colocation_mismatches
 FROM encoded e LEFT JOIN site_history h ON h.site_key=e.site_key GROUP BY 1
)
SELECT * FROM annual ORDER BY year
"""
    # El SELECT final sólo enumera métricas agregadas, no usa SELECT * de RH.
    audit = audit.replace('SELECT * FROM annual','SELECT '+','.join([
        'year','person_snapshots','employee_count','duplicate_source_keys','manager_matches',
        'manager_unmatched','multiple_manager_matches','wrong_snapshot_matches','mapping_conflict_rows',
        'rows_site_multiple_historical_cities','rows_site_multiple_historical_zones','colocation_observable',
        'timezone_observable','same_site_rows','up_to_four_hours_rows','over_four_hours_rows',
        'invalid_pair_used','independent_formula_mismatches','colocation_mismatches'])+' FROM annual')
    audit_path.write_text((prefix+audit).replace('__PERIOD_START__','2020-07-26').replace('__PERIOD_END__','2026-09-07'),encoding='utf-8')
    contract = dict(schema_version=4,id='timezone',title='Proximidad registrada y diferencia horaria del manager',
        claim='La relación usa empleado y manager de la misma foto y respeta los offsets históricos IANA.',
        use='Probar las representaciones geográficas del V11 sobre B completo.',semantic_type='derived_feature',
        population='Employee, Regular, activo, Engineering, sin RF360',grain='persona-foto',
        known_at='Ubicación de la foto; geografía pública estática 2026, usada como proxy retrospectivo declarado.',
        window='2020-07-26 a 2026-09-07',history='V11 aporta una preparación geográfica descriptiva; se incorpora su proxy, con conflictos de zona explícitos y sin asumir vigencia histórica de direcciones.',
        query=audit_path.relative_to(ROOT).as_posix(),source_query=source_path.relative_to(ROOT).as_posix(),
        zero_fields=['duplicate_source_keys','multiple_manager_matches','wrong_snapshot_matches','invalid_pair_used','independent_formula_mismatches','colocation_mismatches'],
        positive_fields=['person_snapshots','colocation_observable','timezone_observable'],expected_rows=7,
        acceptance_rule='Cero duplicados, uniones fuera de fecha, pares inválidos usados o diferencias de cálculo. Mapping ambiguo sigue unknown; sitio igual precede a diferencia horaria.',
        conclusion_if_pass='El proxy puede probarse con su limitación geográfica explícita',
        limitation='Sitio igual no prueba presencia física; catálogo 2026 sin vigencia histórica de direcciones. No cambia score.',
        action='Probar las dos representaciones y conservar missingness',catalog_diagnostics=diagnostics,
        catalog=geo.CATALOG.relative_to(ROOT).as_posix())
    contract_path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Control independiente de offsets con zoneinfo, incluso fechas cercanas a DST.
    cases=[]
    for year in range(2020,2027):
        for month,day in [(1,15),(3,8),(7,15),(11,1)]:
            instant=datetime(year,month,day,12,tzinfo=timezone.utc)
            for zone in sorted(set(sites.values())|set(cities.values())):
                minutes=int(instant.astimezone(ZoneInfo(zone)).utcoffset().total_seconds()/60)
                cases.append(f"SELECT TIMESTAMP '{instant:%Y-%m-%d %H:%M:%S}' AS instant,'{zone}'::VARCHAR(64) AS zone_name,{minutes} AS expected_minutes")
    dst_path=ROOT/'queries/audits/engineering_b_v11_timezone_dst_20261011.sql'
    dst_path.write_text('WITH cases AS (\n'+'\nUNION ALL\n'.join(cases)+"\n)\nSELECT COUNT(*) AS cases_checked, SUM(CASE WHEN DATEDIFF(minute,instant,CONVERT_TIMEZONE('UTC',zone_name,instant))<>expected_minutes THEN 1 ELSE 0 END) AS offset_mismatches FROM cases\n",encoding='utf-8')
    control=dict(contract,id='timezone-dst',title='Offsets históricos contrastados con zoneinfo',query=dst_path.relative_to(ROOT).as_posix(),
        expected_rows=1,zero_fields=['offset_mismatches'],positive_fields=['cases_checked'],
        acceptance_rule='Cero diferencias en minutos entre Redshift y zoneinfo en enero, marzo, julio y noviembre de 2020–2026.',
        population='Fechas y zonas de catálogo público; sin filas de RH',grain='zona-fecha',semantic_type='external_source')
    (contract_path.parent/'timezone-dst.json').write_text(json.dumps(control,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'prepared':'timezone','catalog_diagnostics':diagnostics,'offset_cases':len(cases)},ensure_ascii=False))


if __name__=='__main__':
    main()
