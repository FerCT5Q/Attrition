-- Calidad agregada del mapping office_site -> country en el snapshot del slide.
-- Entregable: internal_analysis. No devuelve filas ni identificadores.
-- Cada fila de etiquetas tiene n >= 30; los casos menores se resumen sin etiqueta.

WITH base AS (
  SELECT
    employee_id,
    NULLIF(TRIM(CAST(office_site AS VARCHAR(512))), '') AS office_site,
    NULLIF(TRIM(CAST(country AS VARCHAR(512))), '') AS country
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt = DATE '2026-08-23'
),
site_country_counts AS (
  SELECT
    office_site,
    country,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM base
  WHERE office_site IS NOT NULL
    AND country IS NOT NULL
  GROUP BY office_site, country
),
site_summary AS (
  SELECT
    office_site,
    COUNT(DISTINCT country) AS country_count,
    SUM(employee_count) AS employee_count,
    SUM(CASE WHEN UPPER(country) = 'INDIA' THEN employee_count ELSE 0 END) AS india_employee_count,
    SUM(CASE WHEN UPPER(country) <> 'INDIA' THEN employee_count ELSE 0 END) AS non_india_employee_count,
    SUM(CASE WHEN employee_count >= 30 THEN 1 ELSE 0 END) AS country_pairs_with_at_least_30,
    SUM(CASE WHEN employee_count < 30 THEN 1 ELSE 0 END) AS country_pairs_below_30
  FROM site_country_counts
  GROUP BY office_site
),
summary AS (
  SELECT
    'mapping_summary' AS result_type,
    CAST(NULL AS VARCHAR(512)) AS office_site,
    COUNT(*) AS employee_count,
    COUNT(*) AS office_site_distinct,
    COUNT(CASE WHEN india_employee_count > 0 THEN 1 END) AS sites_with_india,
    COUNT(CASE WHEN non_india_employee_count > 0 THEN 1 END) AS sites_with_non_india,
    SUM(CASE WHEN country_pairs_below_30 > 0 THEN 1 ELSE 0 END) AS sites_with_small_country_pairs
  FROM site_summary
),
india_site AS (
  SELECT
    'india_label_summary' AS result_type,
    office_site,
    employee_count,
    country_count AS office_site_distinct,
    india_employee_count AS sites_with_india,
    non_india_employee_count AS sites_with_non_india,
    country_pairs_below_30 AS sites_with_small_country_pairs
  FROM site_summary
  WHERE office_site = 'INDIA'
),
material_pairs AS (
  SELECT
    'material_site_country_pair' AS result_type,
    office_site,
    employee_count,
    CAST(NULL AS BIGINT) AS office_site_distinct,
    CAST(NULL AS BIGINT) AS sites_with_india,
    CAST(NULL AS BIGINT) AS sites_with_non_india,
    CAST(NULL AS BIGINT) AS sites_with_small_country_pairs
  FROM site_country_counts
  WHERE employee_count >= 30
    AND office_site IN ('INDIA', 'SAN')
)
SELECT
  result_type,
  office_site,
  employee_count,
  office_site_distinct,
  sites_with_india,
  sites_with_non_india,
  sites_with_small_country_pairs
FROM (
  SELECT result_type, office_site, employee_count, office_site_distinct,
         sites_with_india, sites_with_non_india, sites_with_small_country_pairs
  FROM summary
  UNION ALL
  SELECT result_type, office_site, employee_count, office_site_distinct,
         sites_with_india, sites_with_non_india, sites_with_small_country_pairs
  FROM india_site
  UNION ALL
  SELECT result_type, office_site, employee_count, office_site_distinct,
         sites_with_india, sites_with_non_india, sites_with_small_country_pairs
  FROM material_pairs
) evidence
ORDER BY
  CASE result_type WHEN 'mapping_summary' THEN 1 WHEN 'india_label_summary' THEN 2 ELSE 3 END,
  employee_count DESC,
  office_site
LIMIT 100;
