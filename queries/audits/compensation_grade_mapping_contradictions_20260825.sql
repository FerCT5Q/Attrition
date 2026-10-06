-- Contradicciones agregadas para determinar si grade funciona como mapping
-- univoco de level_grouped y management_level.
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
), grade_mapping AS (
    SELECT
        compensation_grade,
        COUNT(DISTINCT level_grouped) AS level_grouped_values,
        COUNT(DISTINCT management_level) AS management_level_values,
        COUNT(DISTINCT employee_id) AS distinct_employees,
        MIN(fis_mo_end_dt) AS first_snapshot,
        MAX(fis_mo_end_dt) AS last_snapshot
    FROM eligible
    GROUP BY 1
)
SELECT
    COUNT(*) AS grades_with_at_least_30_employees,
    SUM(CASE WHEN level_grouped_values = 1 THEN 1 ELSE 0 END) AS grades_with_one_level_grouped,
    SUM(CASE WHEN level_grouped_values > 1 THEN 1 ELSE 0 END) AS grades_with_multiple_level_grouped,
    SUM(CASE WHEN management_level_values = 1 THEN 1 ELSE 0 END) AS grades_with_one_management_level,
    SUM(CASE WHEN management_level_values > 1 THEN 1 ELSE 0 END) AS grades_with_multiple_management_levels
FROM grade_mapping
WHERE distinct_employees >= 30;
