/*
  Validación simple del cálculo de proximidad empleado-manager.

  Población: Employee / Regular / active_status=1 en el snapshot
  2026-08-23.

  La consulta agrega primero una fila por empleado y una fila por manager,
  vuelve a cruzar ambas tablas agregadas por manager_employee_id = employee_id,
  y devuelve únicamente conteos agregados. No devuelve IDs ni valores de sitio.
*/
WITH source_rows AS (
    SELECT
        CAST(w.employee_id AS BIGINT) AS employee_id,
        CAST(w.manager_employee_id AS BIGINT) AS manager_employee_id,
        NULLIF(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '') AS office_site,
        NULLIF(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '') AS city,
        NULLIF(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '') AS country
    FROM hrda.post_hire_monthly_worker_dtls AS w
    WHERE CAST(w.fis_mo_end_dt AS DATE) = DATE '2026-08-23'
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
),
employee_snapshot AS (
    SELECT
        employee_id,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants,
        MAX(manager_employee_id) AS manager_employee_id,
        COUNT(DISTINCT COALESCE(office_site, '<NULL>')) AS office_site_variants,
        MAX(office_site) AS office_site,
        COUNT(DISTINCT COALESCE(city, '<NULL>')) AS city_variants,
        MAX(city) AS city,
        COUNT(DISTINCT COALESCE(country, '<NULL>')) AS country_variants,
        MAX(country) AS country
    FROM source_rows
    GROUP BY employee_id
),
manager_snapshot AS (
    SELECT
        employee_id,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants,
        COUNT(DISTINCT COALESCE(office_site, '<NULL>')) AS office_site_variants,
        MAX(office_site) AS office_site,
        COUNT(DISTINCT COALESCE(city, '<NULL>')) AS city_variants,
        MAX(city) AS city,
        COUNT(DISTINCT COALESCE(country, '<NULL>')) AS country_variants,
        MAX(country) AS country
    FROM source_rows
    GROUP BY employee_id
),
paired AS (
    SELECT
        e.employee_id,
        e.source_row_count AS employee_source_row_count,
        e.manager_id_variants AS employee_manager_id_variants,
        e.manager_employee_id,
        e.office_site_variants AS employee_office_site_variants,
        e.office_site AS employee_office_site,
        e.city AS employee_city,
        e.country AS employee_country,
        m.employee_id AS matched_manager_id,
        m.source_row_count AS manager_source_row_count,
        m.manager_id_variants AS manager_manager_id_variants,
        m.office_site_variants AS manager_office_site_variants,
        m.office_site AS manager_office_site,
        m.city AS manager_city,
        m.country AS manager_country
    FROM employee_snapshot AS e
    LEFT JOIN manager_snapshot AS m
      ON m.employee_id = e.manager_employee_id
),
join_valid_pairs AS (
    SELECT
        employee_office_site_variants,
        employee_office_site,
        employee_city,
        manager_office_site_variants,
        manager_office_site,
        manager_city
    FROM paired
    WHERE employee_source_row_count = 1
      AND employee_manager_id_variants = 1
      AND employee_office_site_variants <= 1
      AND matched_manager_id IS NOT NULL
      AND manager_source_row_count = 1
      AND manager_manager_id_variants = 1
      AND manager_office_site_variants <= 1
),
site_comparable_pairs AS (
    SELECT
        employee_office_site,
        employee_city,
        manager_office_site,
        manager_city
    FROM join_valid_pairs
    WHERE employee_office_site IS NOT NULL
      AND manager_office_site IS NOT NULL
),
summary AS (
    SELECT 'summary' AS row_type, 'grouped_employee_count' AS metric,
           COUNT(*)::BIGINT AS n, CAST(NULL AS BIGINT) AS denominator,
           CAST(NULL AS DECIMAL(18,4)) AS rate_percent
    FROM employee_snapshot
    UNION ALL
    SELECT 'summary', 'employee_source_duplicate_count',
           SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END)::BIGINT, NULL, NULL
    FROM employee_snapshot
    UNION ALL
    SELECT 'summary', 'employee_conflicting_manager_id_count',
           SUM(CASE WHEN manager_id_variants > 1 THEN 1 ELSE 0 END)::BIGINT, NULL, NULL
    FROM employee_snapshot
    UNION ALL
    SELECT 'summary', 'matched_manager_pair_count', COUNT(*)::BIGINT, NULL, NULL
    FROM join_valid_pairs
    UNION ALL
    SELECT 'summary', 'site_comparable_pair_count', COUNT(*)::BIGINT, NULL, NULL
    FROM site_comparable_pairs
    UNION ALL
    SELECT 'summary', 'same_site_and_city_pair_count',
           SUM(CASE WHEN employee_office_site = manager_office_site
                      AND employee_city = manager_city THEN 1 ELSE 0 END)::BIGINT,
           COUNT(*)::BIGINT,
           ROUND(100.0 * SUM(CASE WHEN employee_office_site = manager_office_site
                                    AND employee_city = manager_city THEN 1 ELSE 0 END)
                 / NULLIF(COUNT(*), 0), 4)
    FROM site_comparable_pairs
),
categories AS (
    SELECT 'category' AS row_type, 'same_office_site' AS metric,
           SUM(CASE WHEN employee_office_site = manager_office_site THEN 1 ELSE 0 END)::BIGINT AS n,
           COUNT(*)::BIGINT AS denominator,
           ROUND(100.0 * SUM(CASE WHEN employee_office_site = manager_office_site THEN 1 ELSE 0 END)
                 / NULLIF(COUNT(*), 0), 4) AS rate_percent
    FROM site_comparable_pairs
    UNION ALL
    SELECT 'category', 'different_office_site',
           SUM(CASE WHEN employee_office_site <> manager_office_site THEN 1 ELSE 0 END)::BIGINT,
           COUNT(*)::BIGINT,
           ROUND(100.0 * SUM(CASE WHEN employee_office_site <> manager_office_site THEN 1 ELSE 0 END)
                 / NULLIF(COUNT(*), 0), 4)
    FROM site_comparable_pairs
    UNION ALL
    SELECT 'category', 'same_site_different_city',
           SUM(CASE WHEN employee_office_site = manager_office_site
                      AND employee_city <> manager_city THEN 1 ELSE 0 END)::BIGINT,
           SUM(CASE WHEN employee_office_site = manager_office_site THEN 1 ELSE 0 END)::BIGINT,
           ROUND(100.0 * SUM(CASE WHEN employee_office_site = manager_office_site
                                    AND employee_city <> manager_city THEN 1 ELSE 0 END)
                 / NULLIF(SUM(CASE WHEN employee_office_site = manager_office_site THEN 1 ELSE 0 END), 0), 4)
    FROM site_comparable_pairs
)
SELECT row_type, metric, n, denominator, rate_percent FROM summary
UNION ALL
SELECT row_type, metric, n, denominator, rate_percent FROM categories
ORDER BY row_type, metric;
