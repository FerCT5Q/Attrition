-- Revisión agregada de office_site dentro de India.
-- Entregable: internal_analysis. No devuelve filas ni identificadores.
-- Snapshot: el mismo usado por el HTML (2026-08-23).
-- Población: worker_type='Employee', employee_type='Regular', active_status=1.
-- Claim: verificar si office_site distingue varias oficinas dentro de India.
-- Regla de aceptación: reportar por separado la cardinalidad de office_site,
-- city y office_location; ningún bucket visible puede tener n < 30.

WITH snapshot_base AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    NULLIF(TRIM(CAST(country AS VARCHAR(512))), '') AS country,
    NULLIF(TRIM(CAST(office_site AS VARCHAR(512))), '') AS office_site,
    NULLIF(TRIM(CAST(city AS VARCHAR(512))), '') AS city,
    NULLIF(TRIM(CAST(office_location AS VARCHAR(512))), '') AS office_location
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt = DATE '2026-08-23'
),
india_snapshot AS (
  SELECT
    'snapshot_summary' AS result_type,
    '2026-08-23' AS snapshot_date,
    'India' AS value_label,
    COUNT(DISTINCT employee_id) AS employee_count,
    COUNT(DISTINCT office_site) AS office_site_distinct,
    COUNT(DISTINCT city) AS city_distinct,
    COUNT(DISTINCT office_location) AS office_location_distinct
  FROM snapshot_base
  WHERE UPPER(country) = 'INDIA'
),
india_site_values AS (
  SELECT
    'office_site_value' AS result_type,
    '2026-08-23' AS snapshot_date,
    office_site AS value_label,
    COUNT(DISTINCT employee_id) AS employee_count,
    COUNT(DISTINCT city) AS city_distinct
  FROM snapshot_base
  WHERE UPPER(country) = 'INDIA'
    AND office_site IS NOT NULL
  GROUP BY office_site
  HAVING COUNT(DISTINCT employee_id) >= 30
),
india_city_values AS (
  SELECT
    'city_value' AS result_type,
    '2026-08-23' AS snapshot_date,
    city AS value_label,
    COUNT(DISTINCT employee_id) AS employee_count,
    COUNT(DISTINCT office_site) AS office_site_distinct
  FROM snapshot_base
  WHERE UPPER(country) = 'INDIA'
    AND city IS NOT NULL
  GROUP BY city
  HAVING COUNT(DISTINCT employee_id) >= 30
),
history_base AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    NULLIF(TRIM(CAST(country AS VARCHAR(512))), '') AS country,
    NULLIF(TRIM(CAST(office_site AS VARCHAR(512))), '') AS office_site,
    NULLIF(TRIM(CAST(city AS VARCHAR(512))), '') AS city
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND UPPER(NULLIF(TRIM(CAST(country AS VARCHAR(512))), '')) = 'INDIA'
),
monthly_history AS (
  SELECT
    fis_mo_end_dt,
    COUNT(DISTINCT office_site) AS office_site_distinct,
    COUNT(DISTINCT city) AS city_distinct
  FROM history_base
  GROUP BY fis_mo_end_dt
),
india_history AS (
  SELECT
    'history_summary' AS result_type,
    CAST(MIN(fis_mo_end_dt) AS VARCHAR(10)) || ' to ' || CAST(MAX(fis_mo_end_dt) AS VARCHAR(10)) AS snapshot_date,
    'India' AS value_label,
    COUNT(DISTINCT employee_id) AS employee_count,
    COUNT(DISTINCT office_site) AS office_site_distinct,
    COUNT(DISTINCT city) AS city_distinct,
    COUNT(DISTINCT fis_mo_end_dt) AS snapshots_checked
  FROM history_base
),
evidence AS (
  SELECT
    result_type,
    snapshot_date,
    value_label,
    employee_count,
    office_site_distinct,
    city_distinct,
    office_location_distinct,
    CAST(NULL AS BIGINT) AS snapshots_checked
  FROM india_snapshot
  UNION ALL
  SELECT
    result_type,
    snapshot_date,
    value_label,
    employee_count,
    CAST(NULL AS BIGINT),
    city_distinct,
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT)
  FROM india_site_values
  UNION ALL
  SELECT
    result_type,
    snapshot_date,
    value_label,
    employee_count,
    office_site_distinct,
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT)
  FROM india_city_values
  UNION ALL
  SELECT
    result_type,
    snapshot_date,
    value_label,
    employee_count,
    office_site_distinct,
    city_distinct,
    CAST(NULL AS BIGINT),
    snapshots_checked
  FROM india_history
)
SELECT
  result_type,
  snapshot_date,
  value_label,
  employee_count,
  office_site_distinct,
  city_distinct,
  office_location_distinct,
  snapshots_checked
FROM evidence
ORDER BY
  CASE result_type
    WHEN 'snapshot_summary' THEN 1
    WHEN 'office_site_value' THEN 2
    WHEN 'city_value' THEN 3
    ELSE 4
  END,
  employee_count DESC,
  value_label
LIMIT 100;
