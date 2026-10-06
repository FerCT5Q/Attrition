-- Catalogo empirico del ultimo snapshot disponible dentro del corte.
-- Se muestran solo combinaciones con al menos 30 empleados distintos.
-- No devuelve identificadores ni valores salariales.
WITH latest AS (
    SELECT MAX(fis_mo_end_dt) AS latest_snapshot
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt <= '2026-08-25'
), eligible AS (
    SELECT
        NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') AS compensation_grade,
        NULLIF(TRIM(CAST(job_level_primary_position AS VARCHAR)), '') AS job_level_primary_position,
        NULLIF(TRIM(CAST(level_grouped AS VARCHAR)), '') AS level_grouped,
        NULLIF(TRIM(CAST(management_level AS VARCHAR)), '') AS management_level,
        employee_id
    FROM hrda.post_hire_monthly_worker_dtls
    CROSS JOIN latest
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt = latest.latest_snapshot
      AND NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') IS NOT NULL
      AND NULLIF(TRIM(CAST(job_level_primary_position AS VARCHAR)), '') IS NOT NULL
)
SELECT
    compensation_grade,
    job_level_primary_position,
    level_grouped,
    management_level,
    COUNT(DISTINCT employee_id) AS distinct_employees,
    (SELECT latest_snapshot FROM latest) AS snapshot_date
FROM eligible
GROUP BY 1, 2, 3, 4
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY level_grouped, job_level_primary_position, compensation_grade;
