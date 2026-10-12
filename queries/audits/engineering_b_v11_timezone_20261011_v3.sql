/* Proxy geográfico estático del V11; modelo sólo en RAM.
   Oficinas públicas 2026; ubicación laboral de la propia foto, sin domicilios. */
WITH source AS (
 SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id,
        manager_employee_id, TRIM(eng_or_noneng) AS engineering,
        MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(office_site)), '[^A-Z0-9]+', ''),'')) AS site_key, MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(country)), '[^A-Z0-9]+', ''),'')||'|'||NULLIF(REGEXP_REPLACE(UPPER(TRIM(city)), '[^A-Z0-9]+', ''),'')) AS city_key
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
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
), pairs AS (
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
