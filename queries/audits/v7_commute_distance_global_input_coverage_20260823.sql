-- Auditoría agregada de cobertura global para el proxy de distancia.
-- No devuelve employee_id, nombres, domicilios, ZIPs ni etiquetas de ZIP.
WITH base AS (
    SELECT
        employee_id,
        NULLIF(TRIM(CAST(country AS VARCHAR(128))), '') AS country_value,
        NULLIF(TRIM(CAST(city AS VARCHAR(128))), '') AS city_value,
        NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), '') AS office_value,
        NULLIF(TRIM(CAST(postal_code AS VARCHAR(32))), '') AS postal_value,
        NULLIF(UPPER(TRIM(CAST(work_arrangement AS VARCHAR(128)))), '') AS work_arrangement_value
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-08-23'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
per_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS snapshot_rows,
        COUNT(DISTINCT country_value) AS country_values,
        COUNT(DISTINCT city_value) AS city_values,
        COUNT(DISTINCT office_value) AS office_values,
        COUNT(DISTINCT postal_value) AS postal_values,
        MAX(CASE WHEN work_arrangement_value = 'ONSITE' THEN 1 ELSE 0 END) AS onsite_flag,
        MAX(CASE WHEN work_arrangement_value IS NULL THEN 1 ELSE 0 END) AS missing_work_arrangement_flag
    FROM base
    GROUP BY 1
)
SELECT
    COUNT(*) AS eligible_employees,
    SUM(CASE WHEN postal_values > 0 THEN 1 ELSE 0 END) AS postal_observable_employees,
    SUM(CASE WHEN office_values > 0 THEN 1 ELSE 0 END) AS office_observable_employees,
    SUM(CASE WHEN country_values > 0 AND city_values > 0 AND office_values > 0 AND postal_values > 0 THEN 1 ELSE 0 END) AS complete_location_employees,
    SUM(CASE WHEN postal_values = 0 THEN 1 ELSE 0 END) AS postal_missing_employees,
    SUM(CASE WHEN office_values = 0 THEN 1 ELSE 0 END) AS office_missing_employees,
    SUM(CASE WHEN snapshot_rows > 1 THEN 1 ELSE 0 END) AS multirow_employees,
    MAX(postal_values) AS max_postal_values_per_employee,
    MAX(office_values) AS max_office_values_per_employee,
    COUNT(*) AS eligible_employee_groups,
    SUM(CASE WHEN onsite_flag = 1 THEN 1 ELSE 0 END) AS onsite_employee_groups,
    SUM(CASE WHEN onsite_flag = 0 THEN 1 ELSE 0 END) AS not_onsite_or_unknown_groups,
    SUM(CASE WHEN missing_work_arrangement_flag = 1 THEN 1 ELSE 0 END) AS missing_work_arrangement_groups,
    SUM(CASE WHEN onsite_flag = 1 AND postal_values > 0 THEN 1 ELSE 0 END) AS onsite_postal_observable_employees,
    SUM(CASE WHEN onsite_flag = 1 AND office_values > 0 THEN 1 ELSE 0 END) AS onsite_office_observable_employees,
    SUM(CASE WHEN onsite_flag = 1 AND country_values > 0 AND city_values > 0 AND office_values > 0 AND postal_values > 0 THEN 1 ELSE 0 END) AS onsite_complete_location_employees
FROM per_employee;
