-- Aggregate-only discovery of available Annual Review cycles and promotion flags.
-- Purpose: identify the most recent completed cycle inside the 12-month window
-- ending at the 2026-08-23 workforce snapshot and validate employee-cycle grain.
WITH normalized AS (
    SELECT
        NULLIF(TRIM(CAST(cycle_name AS VARCHAR(160))), '') AS cycle_name,
        NULLIF(TRIM(CAST(employee_id AS VARCHAR(80))), '') AS employee_key,
        UPPER(NULLIF(TRIM(CAST(promotion_yes_no AS VARCHAR(40))), '')) AS promotion_flag,
        NULLIF(TRIM(CAST(grade AS VARCHAR(80))), '') AS grade,
        CAST(last_modified_date AS DATE) AS last_modified_date
    FROM hrda.annual_review_report
),
cycle_employee AS (
    SELECT
        cycle_name,
        employee_key,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(promotion_flag, '<NULL>')) AS promotion_flag_variants,
        COUNT(DISTINCT COALESCE(grade, '<NULL>')) AS grade_variants,
        MAX(CASE WHEN promotion_flag = 'YES' THEN 1 ELSE 0 END) AS promoted,
        MAX(CASE WHEN grade IS NULL THEN 1 ELSE 0 END) AS missing_grade,
        MIN(last_modified_date) AS min_last_modified_date,
        MAX(last_modified_date) AS max_last_modified_date
    FROM normalized
    WHERE cycle_name IS NOT NULL
      AND employee_key IS NOT NULL
    GROUP BY 1, 2
)
SELECT
    cycle_name,
    COUNT(*)::BIGINT AS employee_count,
    SUM(promoted)::BIGINT AS promoted_employee_count,
    ROUND(100.0 * SUM(promoted) / NULLIF(COUNT(*), 0), 4) AS promotion_rate_percent,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END)::BIGINT AS duplicate_employee_count,
    SUM(CASE WHEN promotion_flag_variants > 1 THEN 1 ELSE 0 END)::BIGINT AS conflicting_promotion_flag_count,
    SUM(CASE WHEN grade_variants > 1 THEN 1 ELSE 0 END)::BIGINT AS conflicting_grade_count,
    SUM(missing_grade)::BIGINT AS missing_grade_count,
    MIN(min_last_modified_date) AS min_last_modified_date,
    MAX(max_last_modified_date) AS max_last_modified_date
FROM cycle_employee
GROUP BY 1
HAVING COUNT(*) >= 30
ORDER BY max_last_modified_date DESC, cycle_name DESC;
