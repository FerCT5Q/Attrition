/*
  Slide 29 | aggregate-only | candidate date availability check.

  Purpose
  -------
  Confirm whether another stored date can replace time_in_job_profile_start_date
  for the August 2025 baseline without silently changing the business concept.

  This is a source-availability audit only. levelentrydate is a detailed-level
  entry date, not a job-profile start date, so it cannot be substituted without
  a definition decision and transition validation.
*/
WITH baseline AS (
  SELECT DATE '2025-08-24' AS snapshot_date
),
employee_snapshot AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    b.snapshot_date,
    MAX(CAST(w.time_in_job_profile_start_date AS DATE)) AS time_in_job_profile_start_date,
    MAX(CAST(w.levelentrydate AS DATE)) AS levelentrydate,
    MAX(CAST(w.max_hire_rehire_date AS DATE)) AS max_hire_rehire_date,
    MAX(w.time_in_role) AS time_in_role,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT COALESCE(CAST(w.time_in_job_profile_start_date AS VARCHAR(32)), '<NULL>')) AS job_profile_date_variants,
    COUNT(DISTINCT COALESCE(CAST(w.levelentrydate AS VARCHAR(32)), '<NULL>')) AS level_entry_date_variants,
    COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS hire_rehire_date_variants
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN baseline AS b
  WHERE CAST(w.fis_mo_end_dt AS DATE) = b.snapshot_date
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND COALESCE(w.is_rf360_yes_no, 0) = 0
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2
),
metrics AS (
  SELECT 'baseline_employee_count' AS metric, COUNT(*)::BIGINT AS value FROM employee_snapshot
  UNION ALL SELECT 'valid_time_in_job_profile_start_date_count', SUM(CASE WHEN time_in_job_profile_start_date IS NOT NULL AND time_in_job_profile_start_date <= snapshot_date THEN 1 ELSE 0 END)::BIGINT FROM employee_snapshot
  UNION ALL SELECT 'valid_levelentrydate_count', SUM(CASE WHEN levelentrydate IS NOT NULL AND levelentrydate <= snapshot_date THEN 1 ELSE 0 END)::BIGINT FROM employee_snapshot
  UNION ALL SELECT 'valid_max_hire_rehire_date_count', SUM(CASE WHEN max_hire_rehire_date IS NOT NULL AND max_hire_rehire_date <= snapshot_date THEN 1 ELSE 0 END)::BIGINT FROM employee_snapshot
  UNION ALL SELECT 'valid_time_in_role_count', SUM(CASE WHEN time_in_role IS NOT NULL AND time_in_role >= 0 THEN 1 ELSE 0 END)::BIGINT FROM employee_snapshot
  UNION ALL SELECT 'duplicate_employee_snapshot_count', SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END)::BIGINT FROM employee_snapshot
  UNION ALL SELECT 'conflicting_job_profile_date_count', SUM(CASE WHEN job_profile_date_variants > 1 THEN 1 ELSE 0 END)::BIGINT FROM employee_snapshot
  UNION ALL SELECT 'conflicting_levelentrydate_count', SUM(CASE WHEN level_entry_date_variants > 1 THEN 1 ELSE 0 END)::BIGINT FROM employee_snapshot
  UNION ALL SELECT 'conflicting_hire_rehire_date_count', SUM(CASE WHEN hire_rehire_date_variants > 1 THEN 1 ELSE 0 END)::BIGINT FROM employee_snapshot
)
SELECT metric, value
FROM metrics
ORDER BY metric;
