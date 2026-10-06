/*
  V7 Job family: August 2026 distribution plus trailing-12-month attrition.

  Display population
  ------------------
  Active Regular Employees with a nonblank job_family at the fiscal August
  2026 snapshot (2026-08-23).  The display is Top 20 current families plus
  Other job families.

  Attrition population and outcome
  --------------------------------
  The attrition denominator is the distinct active Regular employee cohort
  with a nonblank job_family at the prior fiscal-August snapshot (2025-08-24).
  Each employee is assigned to the current Top-20 labels using their
  historical job_family; all other historical families are grouped as Other.
  Outcome is at least one strict VOLUNTARY termination with term_date in
  (2025-08-24, 2026-08-23].

  Grain and privacy
  -----------------
  One aggregate summary row plus 21 aggregate display-category rows. Employee
  identifiers are used only inside COUNT(DISTINCT ...) and are never returned.
*/
WITH current_raw AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    NULLIF(TRIM(CAST(job_family AS VARCHAR(512))), '') AS job_family
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE '2026-08-23'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
),
current_quality AS (
  SELECT
    snapshot_date,
    COUNT(*) AS current_source_rows,
    COUNT(DISTINCT employee_id) AS current_distinct_employees,
    COUNT(DISTINCT CASE WHEN job_family IS NOT NULL THEN employee_id END) AS current_observable_employees,
    COUNT(*) - COUNT(DISTINCT employee_id) AS current_duplicate_source_rows
  FROM current_raw
  GROUP BY 1
),
current_family_counts AS (
  SELECT
    snapshot_date,
    job_family,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM current_raw
  WHERE job_family IS NOT NULL
  GROUP BY 1, 2
),
current_ranked AS (
  SELECT
    snapshot_date,
    job_family,
    employee_count,
    ROW_NUMBER() OVER (PARTITION BY snapshot_date ORDER BY employee_count DESC, job_family) AS category_rank
  FROM current_family_counts
),
current_top20 AS (
  SELECT job_family, category_rank
  FROM current_ranked
  WHERE category_rank <= 20
),
current_display AS (
  SELECT
    category_rank AS display_order,
    job_family AS category_label,
    employee_count AS current_employee_count
  FROM current_ranked
  WHERE category_rank <= 20
  UNION ALL
  SELECT
    21 AS display_order,
    'Other job families' AS category_label,
    q.current_observable_employees - SUM(t.employee_count) AS current_employee_count
  FROM current_quality q
  INNER JOIN current_top20 top20
    ON 1 = 1
  INNER JOIN current_family_counts t
    ON t.job_family = top20.job_family
   AND t.snapshot_date = q.snapshot_date
  GROUP BY q.current_observable_employees
),
baseline_raw AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    NULLIF(TRIM(CAST(job_family AS VARCHAR(512))), '') AS job_family
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE '2025-08-24'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
),
baseline_quality AS (
  SELECT
    snapshot_date,
    COUNT(*) AS baseline_source_rows,
    COUNT(DISTINCT employee_id) AS baseline_distinct_employees,
    COUNT(DISTINCT CASE WHEN job_family IS NOT NULL THEN employee_id END) AS baseline_observable_employees,
    COUNT(*) - COUNT(DISTINCT employee_id) AS baseline_duplicate_source_rows,
    COUNT(DISTINCT CASE
      WHEN job_family IS NOT NULL THEN employee_id || '|' || job_family
    END) - COUNT(DISTINCT CASE WHEN job_family IS NOT NULL THEN employee_id END) AS baseline_extra_job_family_mappings
  FROM baseline_raw
  GROUP BY 1
),
baseline_snapshot AS (
  SELECT
    employee_id,
    MAX(job_family) AS job_family
  FROM baseline_raw
  WHERE job_family IS NOT NULL
  GROUP BY 1
),
voluntary_events AS (
  SELECT
    employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
  GROUP BY 1, 2
),
baseline_targets AS (
  SELECT
    b.employee_id,
    CASE WHEN t.job_family IS NOT NULL THEN t.job_family ELSE 'Other job families' END AS category_label,
    MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_flag
  FROM baseline_snapshot b
  LEFT JOIN current_top20 t
    ON t.job_family = b.job_family
  LEFT JOIN voluntary_events v
    ON v.employee_id = b.employee_id
   AND v.term_date > DATE '2025-08-24'
   AND v.term_date <= DATE '2026-08-23'
  GROUP BY 1, 2
),
category_metrics AS (
  SELECT
    category_label,
    COUNT(*) AS baseline_employee_count,
    SUM(voluntary_exit_flag) AS voluntary_exit_count,
    ROUND(100.0 * SUM(voluntary_exit_flag) / NULLIF(COUNT(*), 0), 4) AS trailing_12m_voluntary_attrition_rate_percent
  FROM baseline_targets
  GROUP BY 1
),
summary AS (
  SELECT
    'summary' AS row_type,
    q.current_snapshot_date,
    q.baseline_snapshot_date,
    q.outcome_cutoff_date,
    q.current_source_rows,
    q.current_distinct_employees,
    q.current_observable_employees,
    q.current_duplicate_source_rows,
    b.baseline_source_rows,
    b.baseline_distinct_employees,
    b.baseline_observable_employees,
    b.baseline_duplicate_source_rows,
    b.baseline_extra_job_family_mappings,
    CAST(NULL AS INTEGER) AS display_order,
    CAST(NULL AS VARCHAR(512)) AS category_label,
    CAST(NULL AS BIGINT) AS current_employee_count,
    CAST(NULL AS BIGINT) AS baseline_employee_count,
    CAST(NULL AS BIGINT) AS voluntary_exit_count,
    CAST(NULL AS DECIMAL(18, 4)) AS trailing_12m_voluntary_attrition_rate_percent
  FROM (
    SELECT
      DATE '2026-08-23' AS current_snapshot_date,
      DATE '2025-08-24' AS baseline_snapshot_date,
      DATE '2026-08-23' AS outcome_cutoff_date,
      current_source_rows,
      current_distinct_employees,
      current_observable_employees,
      current_duplicate_source_rows
    FROM current_quality
  ) q
  CROSS JOIN baseline_quality b
),
categories AS (
  SELECT
    'category' AS row_type,
    DATE '2026-08-23' AS current_snapshot_date,
    DATE '2025-08-24' AS baseline_snapshot_date,
    DATE '2026-08-23' AS outcome_cutoff_date,
    CAST(NULL AS BIGINT) AS current_source_rows,
    CAST(NULL AS BIGINT) AS current_distinct_employees,
    CAST(NULL AS BIGINT) AS current_observable_employees,
    CAST(NULL AS BIGINT) AS current_duplicate_source_rows,
    CAST(NULL AS BIGINT) AS baseline_source_rows,
    CAST(NULL AS BIGINT) AS baseline_distinct_employees,
    CAST(NULL AS BIGINT) AS baseline_observable_employees,
    CAST(NULL AS BIGINT) AS baseline_duplicate_source_rows,
    CAST(NULL AS BIGINT) AS baseline_extra_job_family_mappings,
    d.display_order,
    d.category_label,
    d.current_employee_count,
    COALESCE(m.baseline_employee_count, 0) AS baseline_employee_count,
    COALESCE(m.voluntary_exit_count, 0) AS voluntary_exit_count,
    m.trailing_12m_voluntary_attrition_rate_percent
  FROM current_display d
  LEFT JOIN category_metrics m
    ON m.category_label = d.category_label
)
SELECT
  row_type, current_snapshot_date, baseline_snapshot_date, outcome_cutoff_date,
  current_source_rows, current_distinct_employees, current_observable_employees,
  current_duplicate_source_rows, baseline_source_rows, baseline_distinct_employees,
  baseline_observable_employees, baseline_duplicate_source_rows,
  baseline_extra_job_family_mappings, display_order, category_label,
  current_employee_count, baseline_employee_count, voluntary_exit_count,
  trailing_12m_voluntary_attrition_rate_percent
FROM summary
UNION ALL
SELECT
  row_type, current_snapshot_date, baseline_snapshot_date, outcome_cutoff_date,
  current_source_rows, current_distinct_employees, current_observable_employees,
  current_duplicate_source_rows, baseline_source_rows, baseline_distinct_employees,
  baseline_observable_employees, baseline_duplicate_source_rows,
  baseline_extra_job_family_mappings, display_order, category_label,
  current_employee_count, baseline_employee_count, voluntary_exit_count,
  trailing_12m_voluntary_attrition_rate_percent
FROM categories
ORDER BY row_type, display_order;
