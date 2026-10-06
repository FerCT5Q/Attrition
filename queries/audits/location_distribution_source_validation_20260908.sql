-- Validación agregada de la fuente de las dos gráficas de Location.
-- Entregable: internal_analysis. No devuelve filas ni identificadores.
-- Población: worker_type='Employee', employee_type='Regular', active_status=1.
-- Grain: empleado-snapshot; snapshot congelado usado por el HTML: 2026-08-23.
-- Claim: la primera gráfica usa country y la segunda office_site; office_site
-- no debe interpretarse automáticamente como city.
-- Regla de aceptación: los perfiles/top values deben identificar explícitamente
-- los campos usados por el builder y cada bucket publicado debe tener n >= 30.

WITH base AS (
  SELECT
    employee_id,
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
field_profile AS (
  SELECT
    'field_profile' AS result_type,
    'country' AS field_name,
    COUNT(DISTINCT employee_id) AS eligible_employees,
    COUNT(DISTINCT CASE WHEN country IS NOT NULL THEN employee_id END) AS populated_employees,
    COUNT(DISTINCT country) AS distinct_values,
    MIN(LENGTH(country)) AS min_label_length,
    MAX(LENGTH(country)) AS max_label_length
  FROM base
  UNION ALL
  SELECT
    'field_profile',
    'office_site',
    COUNT(DISTINCT employee_id),
    COUNT(DISTINCT CASE WHEN office_site IS NOT NULL THEN employee_id END),
    COUNT(DISTINCT office_site),
    MIN(LENGTH(office_site)),
    MAX(LENGTH(office_site))
  FROM base
  UNION ALL
  SELECT
    'field_profile',
    'city',
    COUNT(DISTINCT employee_id),
    COUNT(DISTINCT CASE WHEN city IS NOT NULL THEN employee_id END),
    COUNT(DISTINCT city),
    MIN(LENGTH(city)),
    MAX(LENGTH(city))
  FROM base
  UNION ALL
  SELECT
    'field_profile',
    'office_location',
    COUNT(DISTINCT employee_id),
    COUNT(DISTINCT CASE WHEN office_location IS NOT NULL THEN employee_id END),
    COUNT(DISTINCT office_location),
    MIN(LENGTH(office_location)),
    MAX(LENGTH(office_location))
  FROM base
),
top_values AS (
  SELECT
    'top_value' AS result_type,
    'country' AS field_name,
    country AS value_label,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM base
  WHERE country IS NOT NULL
  GROUP BY country
  HAVING COUNT(DISTINCT employee_id) >= 30
  QUALIFY ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT employee_id) DESC, country) <= 20
  UNION ALL
  SELECT
    'top_value',
    'office_site',
    office_site,
    COUNT(DISTINCT employee_id)
  FROM base
  WHERE office_site IS NOT NULL
  GROUP BY office_site
  HAVING COUNT(DISTINCT employee_id) >= 30
  QUALIFY ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT employee_id) DESC, office_site) <= 20
  UNION ALL
  SELECT
    'top_value',
    'city',
    city,
    COUNT(DISTINCT employee_id)
  FROM base
  WHERE city IS NOT NULL
  GROUP BY city
  HAVING COUNT(DISTINCT employee_id) >= 30
  QUALIFY ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT employee_id) DESC, city) <= 20
),
site_context AS (
  SELECT
    'office_site_context' AS result_type,
    'office_site' AS field_name,
    office_site AS value_label,
    country AS context_country,
    city AS context_city,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM base
  WHERE UPPER(office_site) IN ('INDIA', 'SAN')
    AND (country IS NOT NULL OR city IS NOT NULL)
  GROUP BY office_site, country, city
  HAVING COUNT(DISTINCT employee_id) >= 30
)
SELECT
  result_type,
  field_name,
  value_label,
  context_country,
  context_city,
  employee_count,
  eligible_employees,
  populated_employees,
  distinct_values,
  min_label_length,
  max_label_length
FROM (
  SELECT
    fp.result_type,
    fp.field_name,
    CAST(NULL AS VARCHAR(512)) AS value_label,
    CAST(NULL AS VARCHAR(512)) AS context_country,
    CAST(NULL AS VARCHAR(512)) AS context_city,
    fp.populated_employees AS employee_count,
    fp.eligible_employees,
    fp.populated_employees,
    fp.distinct_values,
    fp.min_label_length,
    fp.max_label_length
  FROM field_profile fp
  UNION ALL
  SELECT
    tv.result_type,
    tv.field_name,
    tv.value_label,
    CAST(NULL AS VARCHAR(512)),
    CAST(NULL AS VARCHAR(512)),
    tv.employee_count,
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS INTEGER),
    CAST(NULL AS INTEGER)
  FROM top_values tv
  UNION ALL
  SELECT
    sc.result_type,
    sc.field_name,
    sc.value_label,
    sc.context_country,
    sc.context_city,
    sc.employee_count,
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS INTEGER),
    CAST(NULL AS INTEGER)
  FROM site_context sc
) evidence
ORDER BY
  CASE result_type WHEN 'field_profile' THEN 1 WHEN 'top_value' THEN 2 ELSE 3 END,
  field_name,
  employee_count DESC,
  value_label,
  context_country,
  context_city
LIMIT 100;
