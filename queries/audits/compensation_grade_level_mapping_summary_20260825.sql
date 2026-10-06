-- Reconciliacion agregada de Compensation grade con niveles relacionados.
-- Poblacion: empleados regulares activos hasta el corte de conocimiento.
-- Se cuentan empleados distintos y no se devuelven identificadores.
WITH eligible AS (
    SELECT
        NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') AS compensation_grade,
        NULLIF(TRIM(CAST(level_grouped AS VARCHAR)), '') AS level_grouped,
        NULLIF(TRIM(CAST(management_level AS VARCHAR)), '') AS management_level,
        NULLIF(TRIM(CAST(job_level_primary_position AS VARCHAR)), '') AS job_level_primary_position,
        employee_id,
        fis_mo_end_dt
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt <= '2026-08-25'
      AND NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') IS NOT NULL
), grade_summary AS (
    SELECT
        compensation_grade,
        COUNT(DISTINCT employee_id) AS distinct_employees,
        COUNT(DISTINCT level_grouped) AS level_grouped_values,
        COUNT(DISTINCT management_level) AS management_level_values,
        COUNT(DISTINCT job_level_primary_position) AS job_level_values,
        MIN(fis_mo_end_dt) AS first_snapshot,
        MAX(fis_mo_end_dt) AS last_snapshot
    FROM eligible
    GROUP BY 1
)
SELECT
    compensation_grade,
    distinct_employees,
    level_grouped_values,
    management_level_values,
    job_level_values,
    first_snapshot,
    last_snapshot
FROM grade_summary
WHERE distinct_employees >= 30
ORDER BY compensation_grade;
