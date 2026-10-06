/*
  Slide 29 | aggregate-only | Time at detailed level, August baseline and
  trailing 12-month voluntary attrition.

  Claim
  -----
  The detailed-level clock uses the later of levelentrydate and
  max_hire_rehire_date, restricted to employees with a populated
  job_level_primary_position. The August 2025 baseline is followed through
  August 2026 for strict voluntary exits.

  Acceptance rule
  ---------------
  Both August snapshots must exist; every valid visible band must have at
  least 30 employees; employee-snapshot duplicates/conflicts must be zero;
  dates cannot be future-dated; and each rate must reconcile as distinct
  voluntary exits divided by the baseline employee cohort.
*/
WITH august_cutoffs AS (
  SELECT
    DATE '2025-08-24' AS baseline_snapshot_date,
    DATE '2026-08-23' AS outcome_cutoff_date
),
baseline_raw AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    p.baseline_snapshot_date,
    p.outcome_cutoff_date,
    MAX(CAST(w.levelentrydate AS DATE)) AS level_entry_date,
    MAX(CAST(w.max_hire_rehire_date AS DATE)) AS latest_hire_rehire_date,
    MAX(NULLIF(TRIM(CAST(w.job_level_primary_position AS VARCHAR(256))), '')) AS detailed_level,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT COALESCE(CAST(w.levelentrydate AS VARCHAR(32)), '<NULL>')) AS level_entry_variants,
    COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS latest_hire_rehire_variants,
    COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.job_level_primary_position AS VARCHAR(256))), ''), '<NULL>')) AS detailed_level_variants
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
current_raw AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    p.outcome_cutoff_date AS snapshot_date,
    MAX(CAST(w.levelentrydate AS DATE)) AS level_entry_date,
    MAX(CAST(w.max_hire_rehire_date AS DATE)) AS latest_hire_rehire_date,
    MAX(NULLIF(TRIM(CAST(w.job_level_primary_position AS VARCHAR(256))), '')) AS detailed_level,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT COALESCE(CAST(w.levelentrydate AS VARCHAR(32)), '<NULL>')) AS level_entry_variants,
    COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS latest_hire_rehire_variants,
    COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.job_level_primary_position AS VARCHAR(256))), ''), '<NULL>')) AS detailed_level_variants
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN august_cutoffs AS p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.outcome_cutoff_date
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND COALESCE(w.is_rf360_yes_no, 0) = 0
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2
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
baseline_classified AS (
  SELECT
    b.employee_id,
    b.baseline_snapshot_date,
    b.outcome_cutoff_date,
    b.level_entry_date,
    b.latest_hire_rehire_date,
    b.detailed_level,
    b.source_row_count,
    b.level_entry_variants,
    b.latest_hire_rehire_variants,
    b.detailed_level_variants,
    CASE WHEN e.employee_id IS NOT NULL THEN 1 ELSE 0 END AS voluntary_attrition_target,
    CASE
      WHEN b.level_entry_date IS NULL OR b.latest_hire_rehire_date IS NULL
        OR b.level_entry_date > b.baseline_snapshot_date
        OR b.latest_hire_rehire_date > b.baseline_snapshot_date
        OR b.detailed_level IS NULL THEN NULL
      WHEN DATEADD(year, 1, GREATEST(b.level_entry_date, b.latest_hire_rehire_date)) > b.baseline_snapshot_date THEN '<1 year'
      WHEN DATEADD(year, 2, GREATEST(b.level_entry_date, b.latest_hire_rehire_date)) > b.baseline_snapshot_date THEN '1–<2 years'
      WHEN DATEADD(year, 3, GREATEST(b.level_entry_date, b.latest_hire_rehire_date)) > b.baseline_snapshot_date THEN '2–<3 years'
      WHEN DATEADD(year, 5, GREATEST(b.level_entry_date, b.latest_hire_rehire_date)) > b.baseline_snapshot_date THEN '3–<5 years'
      WHEN DATEADD(year, 10, GREATEST(b.level_entry_date, b.latest_hire_rehire_date)) > b.baseline_snapshot_date THEN '5–<10 years'
      ELSE '10+ years'
    END AS detailed_level_band
  FROM baseline_raw AS b
  LEFT JOIN (SELECT DISTINCT employee_id FROM voluntary_events) AS e
    ON e.employee_id = b.employee_id
),
current_classified AS (
  SELECT
    c.employee_id,
    c.snapshot_date,
    c.level_entry_date,
    c.latest_hire_rehire_date,
    c.detailed_level,
    c.source_row_count,
    c.level_entry_variants,
    c.latest_hire_rehire_variants,
    c.detailed_level_variants,
    CASE
      WHEN c.level_entry_date IS NULL OR c.latest_hire_rehire_date IS NULL
        OR c.level_entry_date > c.snapshot_date
        OR c.latest_hire_rehire_date > c.snapshot_date
        OR c.detailed_level IS NULL THEN NULL
      WHEN DATEADD(year, 1, GREATEST(c.level_entry_date, c.latest_hire_rehire_date)) > c.snapshot_date THEN '<1 year'
      WHEN DATEADD(year, 2, GREATEST(c.level_entry_date, c.latest_hire_rehire_date)) > c.snapshot_date THEN '1–<2 years'
      WHEN DATEADD(year, 3, GREATEST(c.level_entry_date, c.latest_hire_rehire_date)) > c.snapshot_date THEN '2–<3 years'
      WHEN DATEADD(year, 5, GREATEST(c.level_entry_date, c.latest_hire_rehire_date)) > c.snapshot_date THEN '3–<5 years'
      WHEN DATEADD(year, 10, GREATEST(c.level_entry_date, c.latest_hire_rehire_date)) > c.snapshot_date THEN '5–<10 years'
      ELSE '10+ years'
    END AS detailed_level_band
  FROM current_raw AS c
),
annual_metrics AS (
  SELECT
    detailed_level_band AS category,
    COUNT(*) AS employee_snapshot_count,
    SUM(voluntary_attrition_target) AS voluntary_exits,
    ROUND(100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS annual_attrition_rate_percent
  FROM baseline_classified
  WHERE detailed_level_band IS NOT NULL
    AND source_row_count = 1
    AND level_entry_variants = 1
    AND latest_hire_rehire_variants = 1
    AND detailed_level_variants = 1
  GROUP BY 1
),
current_metrics AS (
  SELECT
    detailed_level_band AS category,
    COUNT(*) AS employee_count
  FROM current_classified
  WHERE detailed_level_band IS NOT NULL
    AND source_row_count = 1
    AND level_entry_variants = 1
    AND latest_hire_rehire_variants = 1
    AND detailed_level_variants = 1
  GROUP BY 1
),
diagnostics AS (
  SELECT
    'baseline' AS scope,
    COUNT(*) AS employee_snapshot_count,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
    SUM(CASE WHEN level_entry_variants > 1 OR latest_hire_rehire_variants > 1 OR detailed_level_variants > 1 THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count,
    SUM(CASE WHEN level_entry_date IS NULL OR latest_hire_rehire_date IS NULL OR level_entry_date > baseline_snapshot_date OR latest_hire_rehire_date > baseline_snapshot_date OR detailed_level IS NULL THEN 1 ELSE 0 END) AS invalid_or_missing_detailed_level_count,
    MAX(baseline_snapshot_date) AS snapshot_date
  FROM baseline_raw
  UNION ALL
  SELECT
    'current',
    COUNT(*),
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END),
    SUM(CASE WHEN level_entry_variants > 1 OR latest_hire_rehire_variants > 1 OR detailed_level_variants > 1 THEN 1 ELSE 0 END),
    SUM(CASE WHEN level_entry_date IS NULL OR latest_hire_rehire_date IS NULL OR level_entry_date > snapshot_date OR latest_hire_rehire_date > snapshot_date OR detailed_level IS NULL THEN 1 ELSE 0 END),
    MAX(snapshot_date)
  FROM current_raw
)
SELECT
  'annual_category' AS row_type,
  category,
  employee_snapshot_count AS employee_count,
  voluntary_exits,
  annual_attrition_rate_percent,
  CAST(NULL AS VARCHAR(64)) AS diagnostic_metric,
  CAST(NULL AS BIGINT) AS diagnostic_value,
  CAST(NULL AS DATE) AS snapshot_date
FROM annual_metrics
UNION ALL
SELECT
  'current_category', category, employee_count, NULL, NULL, NULL, NULL, DATE '2026-08-23'
FROM current_metrics
UNION ALL
SELECT
  'diagnostic', NULL, NULL, NULL, NULL, scope || '_employee_snapshot_count', employee_snapshot_count, snapshot_date
FROM diagnostics
UNION ALL
SELECT 'diagnostic', NULL, NULL, NULL, NULL, scope || '_duplicate_employee_snapshot_count', duplicate_employee_snapshot_count, snapshot_date FROM diagnostics
UNION ALL
SELECT 'diagnostic', NULL, NULL, NULL, NULL, scope || '_conflicting_employee_snapshot_count', conflicting_employee_snapshot_count, snapshot_date FROM diagnostics
UNION ALL
SELECT 'diagnostic', NULL, NULL, NULL, NULL, scope || '_invalid_or_missing_detailed_level_count', invalid_or_missing_detailed_level_count, snapshot_date FROM diagnostics
ORDER BY 1, 2, 6;
