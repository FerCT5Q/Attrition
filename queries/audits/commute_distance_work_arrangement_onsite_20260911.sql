-- Validacion agregada de la poblacion de Commute distance por work_arrangement.
-- No devuelve filas de empleados ni valores de domicilio.
WITH base AS (
    SELECT
        employee_id,
        NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '') AS work_arrangement_label,
        NULLIF(TRIM(CAST(postal_code AS VARCHAR(64))), '') AS postal_value,
        NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), '') AS office_value
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-09-27'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
summary AS (
    SELECT
        COUNT(DISTINCT employee_id) AS eligible_employees,
        COUNT(DISTINCT CASE WHEN UPPER(work_arrangement_label) = 'ONSITE' THEN employee_id END) AS onsite_employees,
        COUNT(DISTINCT CASE WHEN work_arrangement_label IS NOT NULL AND UPPER(work_arrangement_label) <> 'ONSITE' THEN employee_id END) AS non_onsite_labeled_employees,
        COUNT(DISTINCT CASE WHEN work_arrangement_label IS NULL THEN employee_id END) AS missing_work_arrangement_employees,
        COUNT(DISTINCT CASE WHEN postal_value IS NOT NULL THEN employee_id END) AS postal_observable_employees,
        COUNT(DISTINCT CASE WHEN office_value IS NOT NULL THEN employee_id END) AS office_observable_employees,
        COUNT(DISTINCT CASE WHEN postal_value IS NOT NULL AND office_value IS NOT NULL THEN employee_id END) AS complete_location_employees
    FROM base
)
SELECT
    eligible_employees,
    onsite_employees,
    non_onsite_labeled_employees,
    missing_work_arrangement_employees,
    postal_observable_employees,
    office_observable_employees,
    complete_location_employees,
    eligible_employees - onsite_employees AS not_onsite_or_unknown_employees,
    eligible_employees - (onsite_employees + non_onsite_labeled_employees + missing_work_arrangement_employees) AS reconciliation_gap
FROM summary;
