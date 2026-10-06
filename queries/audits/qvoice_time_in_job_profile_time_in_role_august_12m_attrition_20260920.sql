/*
  Slide 29 | aggregate-only | August baseline and trailing 12-month outcome.

  Claim
  -----
  Time in job profile and Time in role are assigned at the latest August 2025
  active Regular Employee snapshot. Each band is compared with strict
  voluntary exits after that baseline and through the latest August 2026
  snapshot.

  Regla de aceptación
  -------------------
  The two August snapshots must exist; every valid visible band must have at
  least 30 employees; baseline employee-snapshot duplicates/conflicts and
  invalid dates/negative Time in role must be zero; each rate must reconcile as
  distinct voluntary exits divided by the baseline employee cohort.

  The query returns aggregate rows only. Employee IDs remain inside CTEs for
  the employee-snapshot grain and time-safe outcome join.
*/
WITH august_cutoffs AS (
  SELECT
    MAX(CASE WHEN CAST(fiscal_year AS INTEGER) = 2025 THEN CAST(fis_mo_end_dt AS DATE) END) AS baseline_snapshot_date,
    MAX(CASE WHEN CAST(fiscal_year AS INTEGER) = 2026 THEN CAST(fis_mo_end_dt AS DATE) END) AS outcome_cutoff_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE EXTRACT(MONTH FROM CAST(fis_mo_end_dt AS DATE)) = 8
),
baseline_raw AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    p.baseline_snapshot_date,
    p.outcome_cutoff_date,
    MAX(CAST(w.time_in_job_profile_start_date AS DATE)) AS job_profile_start_date,
    MAX(CAST(w.max_hire_rehire_date AS DATE)) AS latest_hire_rehire_date,
    MAX(w.time_in_role) AS time_in_role_years,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT COALESCE(CAST(w.time_in_job_profile_start_date AS VARCHAR(32)), '<NULL>')) AS job_profile_start_variants,
    COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS latest_hire_rehire_variants,
    COUNT(DISTINCT COALESCE(CAST(w.time_in_role AS VARCHAR(64)), '<NULL>')) AS time_in_role_variants
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN august_cutoffs AS p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_snapshot_date
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND COALESCE(w.is_rf360_yes_no, 0) = 0
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2, 3
),
voluntary_events AS (
  SELECT DISTINCT
    CAST(employee_id AS BIGINT) AS employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN august_cutoffs AS p
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > p.baseline_snapshot_date
    AND CAST(w.term_date AS DATE) <= p.outcome_cutoff_date
    AND w.employee_id IS NOT NULL
),
baseline_cohort AS (
  SELECT
    b.employee_id,
    b.baseline_snapshot_date,
    b.outcome_cutoff_date,
    b.job_profile_start_date,
    b.latest_hire_rehire_date,
    b.time_in_role_years,
    b.source_row_count,
    b.job_profile_start_variants,
    b.latest_hire_rehire_variants,
    b.time_in_role_variants,
    CASE WHEN e.employee_id IS NOT NULL THEN 1 ELSE 0 END AS voluntary_attrition_target
  FROM baseline_raw AS b
  LEFT JOIN (SELECT DISTINCT employee_id FROM voluntary_events) AS e
    ON e.employee_id = b.employee_id
),
classified AS (
  SELECT
    baseline_snapshot_date,
    outcome_cutoff_date,
    employee_id,
    source_row_count,
    job_profile_start_variants,
    latest_hire_rehire_variants,
    time_in_role_variants,
    voluntary_attrition_target,
    CASE
      WHEN job_profile_start_date IS NULL OR latest_hire_rehire_date IS NULL
        OR job_profile_start_date > baseline_snapshot_date
        OR latest_hire_rehire_date > baseline_snapshot_date THEN NULL
      WHEN DATEADD(year, 1, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > baseline_snapshot_date THEN '<1 year'
      WHEN DATEADD(year, 2, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > baseline_snapshot_date THEN '1–<2 years'
      WHEN DATEADD(year, 3, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > baseline_snapshot_date THEN '2–<3 years'
      WHEN DATEADD(year, 5, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > baseline_snapshot_date THEN '3–<5 years'
      WHEN DATEADD(year, 10, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > baseline_snapshot_date THEN '5–<10 years'
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
  FROM baseline_cohort
),
category_rows AS (
  SELECT 'time_in_job_profile' AS metric, time_in_job_profile_band AS category, employee_id, voluntary_attrition_target
  FROM classified
  WHERE time_in_job_profile_band IS NOT NULL
    AND source_row_count = 1
    AND job_profile_start_variants = 1
    AND latest_hire_rehire_variants = 1
  UNION ALL
  SELECT 'time_in_role' AS metric, time_in_role_band AS category, employee_id, voluntary_attrition_target
  FROM classified
  WHERE time_in_role_band IS NOT NULL
    AND source_row_count = 1
    AND time_in_role_variants = 1
),
category_metrics AS (
  SELECT
    metric,
    category,
    COUNT(*) AS baseline_employee_count,
    SUM(voluntary_attrition_target) AS voluntary_exits,
    ROUND(100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS trailing_12m_voluntary_attrition_rate_percent
  FROM category_rows
  GROUP BY 1, 2
),
diagnostics AS (
  SELECT
    COUNT(*) AS baseline_employee_count,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
    SUM(CASE WHEN job_profile_start_variants > 1 OR latest_hire_rehire_variants > 1 OR time_in_role_variants > 1 THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count,
    SUM(CASE WHEN job_profile_start_date IS NULL OR latest_hire_rehire_date IS NULL OR job_profile_start_date > baseline_snapshot_date OR latest_hire_rehire_date > baseline_snapshot_date THEN 1 ELSE 0 END) AS invalid_or_missing_job_profile_count,
    SUM(CASE WHEN time_in_role_years IS NULL OR time_in_role_years < 0 THEN 1 ELSE 0 END) AS invalid_or_missing_time_in_role_count,
    MAX(baseline_snapshot_date) AS baseline_snapshot_date,
    MAX(outcome_cutoff_date) AS outcome_cutoff_date
  FROM baseline_raw
)
SELECT
  'category' AS row_type,
  metric,
  category,
  baseline_employee_count,
  voluntary_exits,
  trailing_12m_voluntary_attrition_rate_percent,
  CAST(NULL AS BIGINT) AS diagnostic_value,
  CAST(NULL AS DATE) AS baseline_snapshot_date,
  CAST(NULL AS DATE) AS outcome_cutoff_date
FROM category_metrics
UNION ALL
SELECT 'diagnostic', 'baseline_employee_count', NULL, NULL, NULL, NULL, baseline_employee_count, baseline_snapshot_date, outcome_cutoff_date FROM diagnostics
UNION ALL
SELECT 'diagnostic', 'duplicate_employee_snapshot_count', NULL, NULL, NULL, NULL, duplicate_employee_snapshot_count, baseline_snapshot_date, outcome_cutoff_date FROM diagnostics
UNION ALL
SELECT 'diagnostic', 'conflicting_employee_snapshot_count', NULL, NULL, NULL, NULL, conflicting_employee_snapshot_count, baseline_snapshot_date, outcome_cutoff_date FROM diagnostics
UNION ALL
SELECT 'diagnostic', 'invalid_or_missing_job_profile_count', NULL, NULL, NULL, NULL, invalid_or_missing_job_profile_count, baseline_snapshot_date, outcome_cutoff_date FROM diagnostics
UNION ALL
SELECT 'diagnostic', 'invalid_or_missing_time_in_role_count', NULL, NULL, NULL, NULL, invalid_or_missing_time_in_role_count, baseline_snapshot_date, outcome_cutoff_date FROM diagnostics
ORDER BY 1, 2, 3;
