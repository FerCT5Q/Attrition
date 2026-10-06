-- Cruce agregado office_site -> country -> city para el snapshot del slide.
-- Entregable: internal_analysis. No devuelve filas ni identificadores.
-- Snapshot: 2026-08-23; población regular activa.
-- Regla: cada etiqueta visible tiene al menos 30 empleados distintos.

WITH base AS (
  SELECT
    employee_id,
    NULLIF(TRIM(CAST(office_site AS VARCHAR(512))), '') AS office_site,
    NULLIF(TRIM(CAST(country AS VARCHAR(512))), '') AS country,
    NULLIF(TRIM(CAST(city AS VARCHAR(512))), '') AS city
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt = DATE '2026-08-23'
),
site_totals AS (
  SELECT
    office_site,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM base
  WHERE office_site IS NOT NULL
  GROUP BY office_site
),
site_country AS (
  SELECT
    office_site,
    country,
    COUNT(DISTINCT employee_id) AS employee_count,
    COUNT(DISTINCT city) AS city_count
  FROM base
  WHERE office_site IS NOT NULL
    AND country IS NOT NULL
  GROUP BY office_site, country
  HAVING COUNT(DISTINCT employee_id) >= 30
),
site_city AS (
  SELECT
    office_site,
    country,
    city,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM base
  WHERE office_site IN ('INDIA', 'SAN')
    AND country IS NOT NULL
    AND city IS NOT NULL
  GROUP BY office_site, country, city
  HAVING COUNT(DISTINCT employee_id) >= 30
),
summary AS (
  SELECT
    'summary' AS result_type,
    CAST(NULL AS VARCHAR(512)) AS office_site,
    CAST(NULL AS VARCHAR(512)) AS country,
    CAST(NULL AS VARCHAR(512)) AS city,
    COUNT(DISTINCT employee_id) AS employee_count,
    COUNT(DISTINCT office_site) AS office_site_distinct,
    COUNT(DISTINCT CASE WHEN UPPER(country) = 'INDIA' THEN office_site END) AS office_sites_with_india,
    COUNT(DISTINCT CASE WHEN UPPER(country) <> 'INDIA' THEN office_site END) AS office_sites_with_non_india
  FROM base
),
site_country_rows AS (
  SELECT
    'office_site_country' AS result_type,
    sc.office_site,
    sc.country,
    CAST(NULL AS VARCHAR(512)) AS city,
    sc.employee_count,
    CAST(NULL AS BIGINT) AS office_site_distinct,
    CAST(NULL AS BIGINT) AS office_sites_with_india,
    sc.city_count AS office_sites_with_non_india
  FROM site_country sc
  JOIN (
    SELECT office_site
    FROM site_totals
    ORDER BY employee_count DESC, office_site
    LIMIT 20
  ) top_sites
    ON top_sites.office_site = sc.office_site
),
site_city_rows AS (
  SELECT
    'office_site_city' AS result_type,
    office_site,
    country,
    city,
    employee_count,
    CAST(NULL AS BIGINT) AS office_site_distinct,
    CAST(NULL AS BIGINT) AS office_sites_with_india,
    CAST(NULL AS BIGINT) AS office_sites_with_non_india
  FROM site_city
)
SELECT
  result_type,
  office_site,
  country,
  city,
  employee_count,
  office_site_distinct,
  office_sites_with_india,
  office_sites_with_non_india
FROM (
  SELECT result_type, office_site, country, city, employee_count,
         office_site_distinct, office_sites_with_india, office_sites_with_non_india
  FROM summary
  UNION ALL
  SELECT result_type, office_site, country, city, employee_count,
         office_site_distinct, office_sites_with_india, office_sites_with_non_india
  FROM site_country_rows
  UNION ALL
  SELECT result_type, office_site, country, city, employee_count,
         office_site_distinct, office_sites_with_india, office_sites_with_non_india
  FROM site_city_rows
) evidence
ORDER BY
  CASE result_type WHEN 'summary' THEN 1 WHEN 'office_site_country' THEN 2 ELSE 3 END,
  employee_count DESC,
  office_site,
  country,
  city
LIMIT 100;
