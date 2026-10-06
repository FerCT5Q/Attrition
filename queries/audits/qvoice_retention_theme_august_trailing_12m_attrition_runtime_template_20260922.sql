/*
  Aggregate-only runtime template for Jan-2026 QVoice improvement themes.

  The builder replaces SOURCE_JSON, DISPLAY_SNAPSHOT, BASELINE_SNAPSHOT, and
  AUGUST_CUTOFF_DATE in memory. The expanded SQL is never persisted. The
  result contains only one aggregate row per group_code.

  source_employee_count is the Jan-2026 source membership count. The
  attrition denominator is restricted to employees active at both the
  pre-wave display snapshot and the August-2025 baseline snapshot. Themes
  are non-exclusive; each group is calculated independently.
*/
WITH source AS (
  SELECT elem.employee_id::BIGINT AS employee_id,
         elem.group_code::INTEGER AS group_code
  FROM (SELECT JSON_PARSE('SOURCE_JSON') AS payload) AS src,
       src.payload AS elem
), display_baseline AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE 'DISPLAY_SNAPSHOT'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
  GROUP BY 1
), attrition_baseline AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE 'BASELINE_SNAPSHOT'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
  GROUP BY 1
), voluntary_events AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND CAST(term_date AS DATE) > DATE 'BASELINE_SNAPSHOT'
    AND CAST(term_date AS DATE) <= DATE 'AUGUST_CUTOFF_DATE'
  GROUP BY 1
)
SELECT s.group_code,
       COUNT(*) AS source_employee_count,
       COUNT(*) - COUNT(DISTINCT s.employee_id) AS source_duplicate_employee_count,
       SUM(CASE WHEN d.employee_id IS NOT NULL AND b.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_employee_count,
       SUM(CASE WHEN d.employee_id IS NOT NULL AND b.employee_id IS NOT NULL AND e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count
FROM source AS s
LEFT JOIN display_baseline AS d
  ON d.employee_id = s.employee_id
LEFT JOIN attrition_baseline AS b
  ON b.employee_id = d.employee_id
LEFT JOIN voluntary_events AS e
  ON e.employee_id = b.employee_id
GROUP BY 1
ORDER BY 1;
