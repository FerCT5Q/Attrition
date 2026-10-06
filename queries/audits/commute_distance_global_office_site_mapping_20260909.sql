-- Auditoría agregada de la semántica operativa de office_site para el cálculo
-- global. No devuelve empleados ni códigos postales residenciales.
WITH base AS (
    SELECT
        employee_id,
        NULLIF(TRIM(CAST(country AS VARCHAR(128))), '') AS country_label,
        NULLIF(TRIM(CAST(city AS VARCHAR(128))), '') AS city_label,
        NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), '') AS office_site_label
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-09-27'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
site_values AS (
    SELECT
        office_site_label,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(DISTINCT country_label) AS country_count,
        COUNT(DISTINCT city_label) AS city_count,
        MIN(country_label) AS example_country,
        MIN(city_label) AS example_city
    FROM base
    WHERE office_site_label IS NOT NULL
    GROUP BY 1
)
SELECT
    office_site_label,
    employee_count,
    country_count,
    city_count,
    example_country,
    example_city
FROM site_values
WHERE employee_count >= 30
ORDER BY employee_count DESC, office_site_label
LIMIT 100;
