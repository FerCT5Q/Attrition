/* Categorías de V11 conocidas en la misma foto. Modo presentation.
   Procesamiento en RAM autorizado; sin domicilios ni motivos sensibles. */
WITH source AS (
 SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id,
        NULLIF(UPPER(TRIM(country)),'') AS country,
        NULLIF(UPPER(TRIM(city)),'') AS city,
        NULLIF(UPPER(TRIM(labor_market)),'') AS market,
        NULLIF(UPPER(TRIM(work_arrangement)),'') AS arrangement,
        NULLIF(UPPER(TRIM(acquisition)),'') AS acquisition
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
 AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
 AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
),
cells AS (
 SELECT snapshot_date,employee_id,COUNT(*) AS source_rows,
        MAX(country) AS country,MAX(city) AS city,MAX(market) AS market,
        MAX(arrangement) AS arrangement,MAX(acquisition) AS acquisition,
        COUNT(DISTINCT COALESCE(country,'<NULL>')||'|'||COALESCE(city,'<NULL>')) AS city_variants,
        COUNT(DISTINCT COALESCE(market,'<NULL>')) AS market_variants,
        COUNT(DISTINCT COALESCE(arrangement,'<NULL>')) AS arrangement_variants,
        COUNT(DISTINCT COALESCE(acquisition,'<NULL>')) AS acquisition_variants
 FROM source GROUP BY 1,2
),
encoded AS (
 SELECT snapshot_date,employee_id,source_rows,city_variants,market_variants,
        arrangement_variants,acquisition_variants,country,city,market,arrangement,acquisition,
        CASE WHEN country IS NOT NULL AND city IS NOT NULL THEN country||' | '||city ELSE '(unknown)' END AS work_city,
        COALESCE(market,'(unknown)') AS labor_market_detail,
        CASE WHEN arrangement IS NULL THEN '(unknown)'
             WHEN arrangement='ONSITE' THEN 'Onsite'
             WHEN arrangement='SHORT-TERM REMOTE WORK' THEN 'Short-Term Remote Work'
             ELSE 'Other offsite arrangements' END AS work_arrangement_v11,
        COALESCE(acquisition,'sin registro') AS acquisition_detail
 FROM cells
)

SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT employee_id) AS employee_count,
 COUNT(DISTINCT snapshot_date) AS snapshots,
 SUM(CASE WHEN source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_keys,
 SUM(CASE WHEN arrangement_variants<>1 THEN 1 ELSE 0 END) AS contradictory_cells,
 SUM(CASE WHEN arrangement IS NOT NULL THEN 1 ELSE 0 END) AS populated_rows,
 MIN(CASE WHEN arrangement IS NOT NULL THEN snapshot_date END) AS first_observed_snapshot,
 COUNT(DISTINCT CASE WHEN arrangement IS NOT NULL THEN work_arrangement_v11 END) AS categories,
 SUM(CASE WHEN NOT(arrangement IS NOT NULL) AND work_arrangement_v11<>'(unknown)' THEN 1 ELSE 0 END) AS missing_encoding_violations,
 SUM(CASE WHEN arrangement='ONSITE' AND work_arrangement_v11<>'Onsite' THEN 1
 WHEN arrangement='SHORT-TERM REMOTE WORK' AND work_arrangement_v11<>'Short-Term Remote Work' THEN 1
 WHEN arrangement NOT IN ('ONSITE','SHORT-TERM REMOTE WORK') AND work_arrangement_v11<>'Other offsite arrangements' THEN 1 ELSE 0 END) AS mapping_violations
FROM encoded GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1;
