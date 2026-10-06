-- Auditoría agregada de entradas para una distancia geodésica aproximada.
-- No devuelve employee_id, postal_code, nombres, domicilios ni hashes.
--
-- Regla de aceptación previa:
-- 1) eligible_employees = 90 en el snapshot objetivo;
-- 2) no debe haber más de una fila por empleado en el snapshot;
-- 3) postal_missing_employees + postal_observable_employees = eligible_employees;
-- 4) la salida final sólo puede publicar bandas n>=30 y sumar la población
--    observable; empleados sin postal_code se reportan como cobertura faltante.
WITH base AS (
    SELECT
        employee_id,
        NULLIF(TRIM(CAST(postal_code AS VARCHAR(32))), '') AS postal_value,
        NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), '') AS office_value
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-09-27'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND UPPER(TRIM(city)) = 'MEXICO CITY'
      AND UPPER(TRIM(country)) = 'MEXICO'
),
employee_cardinality AS (
    SELECT
        employee_id,
        COUNT(*) AS snapshot_rows,
        COUNT(DISTINCT postal_value) AS postal_value_count,
        COUNT(DISTINCT office_value) AS office_value_count
    FROM base
    GROUP BY 1
),
summary AS (
    SELECT
        COUNT(*) AS eligible_employees,
        SUM(CASE WHEN postal_value_count > 0 THEN 1 ELSE 0 END) AS postal_observable_employees,
        SUM(CASE WHEN postal_value_count = 0 THEN 1 ELSE 0 END) AS postal_missing_employees,
        SUM(CASE WHEN office_value_count > 0 THEN 1 ELSE 0 END) AS office_observable_employees,
        SUM(CASE WHEN postal_value_count > 0 AND office_value_count > 0 THEN 1 ELSE 0 END) AS both_observable_employees,
        SUM(CASE WHEN snapshot_rows > 1 THEN 1 ELSE 0 END) AS multirow_employees,
        COUNT(DISTINCT CASE WHEN postal_value_count > 0 THEN postal_value_count END) AS distinct_postal_cardinality_counts,
        MAX(postal_value_count) AS max_postal_values_per_employee,
        MAX(office_value_count) AS max_office_values_per_employee
    FROM employee_cardinality
)
SELECT
    DATE '2026-09-27' AS snapshot_date,
    'MEXICO CITY' AS city_label,
    'MEXICO' AS country_label,
    eligible_employees,
    postal_observable_employees,
    postal_missing_employees,
    office_observable_employees,
    both_observable_employees,
    multirow_employees,
    distinct_postal_cardinality_counts,
    max_postal_values_per_employee,
    max_office_values_per_employee
FROM summary;
