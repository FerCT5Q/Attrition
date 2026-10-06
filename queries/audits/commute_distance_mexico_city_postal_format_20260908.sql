-- Auditoría agregada de formato del postal_code residencial.
-- No devuelve códigos postales ni hashes; sólo evalúa si el valor observado
-- tiene el formato postal mexicano esperado para el catálogo de referencia.
WITH base AS (
    SELECT
        employee_id,
        NULLIF(TRIM(CAST(postal_code AS VARCHAR(32))), '') AS postal_value
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-09-27'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND UPPER(TRIM(city)) = 'MEXICO CITY'
      AND UPPER(TRIM(country)) = 'MEXICO'
),
per_employee AS (
    SELECT
        employee_id,
        MAX(postal_value) AS postal_value
    FROM base
    GROUP BY 1
)
SELECT
    COUNT(*) AS eligible_employees,
    COUNT(CASE WHEN postal_value IS NULL THEN 1 END) AS null_or_blank_employees,
    COUNT(CASE WHEN postal_value IS NOT NULL AND LEN(postal_value) = 5 THEN 1 END) AS length_5_employees,
    COUNT(CASE WHEN postal_value IS NOT NULL AND postal_value ~ '^[0-9]{5}$' THEN 1 END) AS numeric_5_employees,
    COUNT(CASE WHEN postal_value IS NOT NULL AND NOT (postal_value ~ '^[0-9]{5}$') THEN 1 END) AS non_numeric_or_non5_employees,
    MIN(CASE WHEN postal_value IS NOT NULL THEN LEN(postal_value) END) AS min_nonblank_length,
    MAX(CASE WHEN postal_value IS NOT NULL THEN LEN(postal_value) END) AS max_nonblank_length
FROM per_employee;
