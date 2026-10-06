-- Catalogo empirico agregado: grade, job level y bandas de nivel observadas.
-- Se muestran solo combinaciones con al menos 30 empleados distintos.
-- No devuelve identificadores ni valores salariales.
WITH eligible AS (
    SELECT
        NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') AS compensation_grade,
        NULLIF(TRIM(CAST(job_level_primary_position AS VARCHAR)), '') AS job_level_primary_position,
        NULLIF(TRIM(CAST(level_grouped AS VARCHAR)), '') AS level_grouped,
        NULLIF(TRIM(CAST(management_level AS VARCHAR)), '') AS management_level,
        employee_id,
        fis_mo_end_dt
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt <= '2026-08-25'
      AND NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') IS NOT NULL
      AND NULLIF(TRIM(CAST(job_level_primary_position AS VARCHAR)), '') IS NOT NULL
), catalog AS (
    SELECT
        compensation_grade,
        job_level_primary_position,
        level_grouped,
        management_level,
        COUNT(DISTINCT employee_id) AS distinct_employees,
        MIN(fis_mo_end_dt) AS first_snapshot,
        MAX(fis_mo_end_dt) AS last_snapshot
    FROM eligible
    GROUP BY 1, 2, 3, 4
)
SELECT
    compensation_grade,
    job_level_primary_position,
    level_grouped,
    management_level,
    distinct_employees,
    first_snapshot,
    last_snapshot
FROM catalog
WHERE distinct_employees >= 30
ORDER BY level_grouped, job_level_primary_position, compensation_grade;
