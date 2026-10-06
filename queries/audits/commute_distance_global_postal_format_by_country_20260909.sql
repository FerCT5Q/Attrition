-- Perfil agregado de formato postal por país para diagnosticar cobertura del
-- cruce con centroides públicos. No devuelve códigos postales individuales.
WITH base AS (
    SELECT
        employee_id,
        NULLIF(TRIM(CAST(country AS VARCHAR(128))), '') AS country_label,
        NULLIF(TRIM(CAST(postal_code AS VARCHAR(32))), '') AS postal_value
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-09-27'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
profile AS (
    SELECT
        country_label,
        CASE
            WHEN postal_value ~ '^[0-9]+$' THEN 'digits_only'
            WHEN postal_value ~ '^[A-Za-z0-9]+$' THEN 'alphanumeric_no_separator'
            WHEN postal_value ~ '^[A-Za-z0-9]+[ -][A-Za-z0-9]+$' THEN 'alphanumeric_with_separator'
            ELSE 'other_format'
        END AS postal_format,
        COUNT(DISTINCT employee_id) AS employee_count,
        MIN(LENGTH(postal_value)) AS min_length,
        MAX(LENGTH(postal_value)) AS max_length
    FROM base
    WHERE country_label IS NOT NULL
      AND postal_value IS NOT NULL
    GROUP BY 1, 2
)
SELECT country_label, postal_format, employee_count, min_length, max_length
FROM profile
WHERE employee_count >= 30
ORDER BY country_label, employee_count DESC;
