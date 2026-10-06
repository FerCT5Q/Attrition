-- Relaciones agregadas observadas entre Compensation grade y bandas de nivel.
-- Una fila resume una combinacion grade-level con al menos 30 empleados distintos.
WITH eligible AS (
    SELECT
        NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') AS compensation_grade,
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
      AND NULLIF(TRIM(CAST(level_grouped AS VARCHAR)), '') IS NOT NULL
      AND NULLIF(TRIM(CAST(management_level AS VARCHAR)), '') IS NOT NULL
)
SELECT
    compensation_grade,
    level_grouped,
    management_level,
    COUNT(DISTINCT employee_id) AS distinct_employees,
    COUNT(*) AS worker_month_rows,
    MIN(fis_mo_end_dt) AS first_snapshot,
    MAX(fis_mo_end_dt) AS last_snapshot
FROM eligible
GROUP BY 1, 2, 3
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY compensation_grade, distinct_employees DESC, level_grouped, management_level;
