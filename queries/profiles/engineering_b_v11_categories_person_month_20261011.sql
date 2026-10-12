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
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '__PERIOD_START__' AND DATE '__PERIOD_END__'
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
-- MODEL_OUTPUT
SELECT snapshot_date,MD5(CAST(employee_id AS VARCHAR)||'__RUN_SALT__') AS person_key,
       work_city,labor_market_detail,work_arrangement_v11,acquisition_detail
FROM encoded
