/*
  Slide 29 | aggregate-only | current August distribution.

  Purpose
  -------
  Provide the current distribution shown beside the August trailing-12-month
  cohort rates. The query returns category aggregates and source-quality
  diagnostics only; employee_id is retained only inside the employee-snapshot
  CTE for deduplication.

  Acceptance rule
  ---------------
  The 2026-08-23 snapshot must exist; each displayed band must have at least
  30 employees; duplicate/conflicting employee snapshots must be zero; and
  invalid dates or negative time_in_role values must be reported separately.
*/
WITH snapshot_cutoff AS (
  SELECT DATE '2026-08-23' AS snapshot_date
),
snapshot_raw AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    s.snapshot_date,
    MAX(CAST(w.time_in_job_profile_start_date AS DATE)) AS job_profile_start_date,
    MAX(CAST(w.max_hire_rehire_date AS DATE)) AS latest_hire_rehire_date,
    MAX(w.time_in_role) AS time_in_role_years,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT COALESCE(CAST(w.time_in_job_profile_start_date AS VARCHAR(32)), '<NULL>')) AS job_profile_start_variants,
    COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS latest_hire_rehire_variants,
    COUNT(DISTINCT COALESCE(CAST(w.time_in_role AS VARCHAR(64)), '<NULL>')) AS time_in_role_variants
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN snapshot_cutoff AS s
  WHERE CAST(w.fis_mo_end_dt AS DATE) = s.snapshot_date
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND COALESCE(w.is_rf360_yes_no, 0) = 0
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2
),
classified AS (
  SELECT
    snapshot_date,
    employee_id,
    source_row_count,
    job_profile_start_variants,
    latest_hire_rehire_variants,
    time_in_role_variants,
    CASE
      WHEN job_profile_start_date IS NULL OR latest_hire_rehire_date IS NULL
        OR job_profile_start_date > snapshot_date
        OR latest_hire_rehire_date > snapshot_date THEN NULL
      WHEN DATEADD(year, 1, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > snapshot_date THEN '<1 year'
      WHEN DATEADD(year, 2, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > snapshot_date THEN '1–<2 years'
      WHEN DATEADD(year, 3, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > snapshot_date THEN '2–<3 years'
      WHEN DATEADD(year, 5, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > snapshot_date THEN '3–<5 years'
      WHEN DATEADD(year, 10, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > snapshot_date THEN '5–<10 years'
      ELSE '10+ years'
    END AS time_in_job_profile_band,
    CASE
      WHEN time_in_role_years IS NULL OR time_in_role_years < 0 THEN NULL
      WHEN time_in_role_years < 1 THEN '<1 year'
      WHEN time_in_role_years < 2 THEN '1–<2 years'
      WHEN time_in_role_years < 3 THEN '2–<3 years'
      WHEN time_in_role_years < 5 THEN '3–<5 years'
      WHEN time_in_role_years < 10 THEN '5–<10 years'
      ELSE '10+ years'
    END AS time_in_role_band
  FROM snapshot_raw
),
category_rows AS (
  SELECT 'time_in_job_profile' AS metric, time_in_job_profile_band AS category, employee_id
  FROM classified
  WHERE time_in_job_profile_band IS NOT NULL
    AND source_row_count = 1
    AND job_profile_start_variants = 1
    AND latest_hire_rehire_variants = 1
  UNION ALL
  SELECT 'time_in_role' AS metric, time_in_role_band AS category, employee_id
  FROM classified
  WHERE time_in_role_band IS NOT NULL
    AND source_row_count = 1
    AND time_in_role_variants = 1
),
category_metrics AS (
  SELECT metric, category, COUNT(*) AS employee_count
  FROM category_rows
  GROUP BY 1, 2
),
diagnostics AS (
  SELECT
    COUNT(*) AS snapshot_employee_count,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
    SUM(CASE WHEN job_profile_start_variants > 1 OR latest_hire_rehire_variants > 1 OR time_in_role_variants > 1 THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count,
    SUM(CASE WHEN job_profile_start_date IS NULL OR latest_hire_rehire_date IS NULL OR job_profile_start_date > snapshot_date OR latest_hire_rehire_date > snapshot_date THEN 1 ELSE 0 END) AS invalid_or_missing_job_profile_count,
    SUM(CASE WHEN time_in_role_years IS NULL OR time_in_role_years < 0 THEN 1 ELSE 0 END) AS invalid_or_missing_time_in_role_count,
    MAX(snapshot_date) AS snapshot_date
  FROM snapshot_raw
)
SELECT
  'category' AS row_type,
  metric,
  category,
  employee_count,
  CAST(NULL AS BIGINT) AS diagnostic_value,
  CAST(NULL AS DATE) AS snapshot_date
FROM category_metrics
UNION ALL
SELECT 'diagnostic', 'snapshot_employee_count', NULL, NULL, snapshot_employee_count, snapshot_date FROM diagnostics
UNION ALL
SELECT 'diagnostic', 'duplicate_employee_snapshot_count', NULL, NULL, duplicate_employee_snapshot_count, snapshot_date FROM diagnostics
UNION ALL
SELECT 'diagnostic', 'conflicting_employee_snapshot_count', NULL, NULL, conflicting_employee_snapshot_count, snapshot_date FROM diagnostics
UNION ALL
SELECT 'diagnostic', 'invalid_or_missing_job_profile_count', NULL, NULL, invalid_or_missing_job_profile_count, snapshot_date FROM diagnostics
UNION ALL
SELECT 'diagnostic', 'invalid_or_missing_time_in_role_count', NULL, NULL, invalid_or_missing_time_in_role_count, snapshot_date FROM diagnostics
ORDER BY 1, 2, 3;
