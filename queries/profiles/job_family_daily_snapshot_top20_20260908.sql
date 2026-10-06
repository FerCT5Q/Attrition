-- Claim: the Job Family panel can use the 2026-09-07 daily employee snapshot
-- as the post-weekend, pre-reorganization comparison point.
-- Semantic type: direct field at employee-day snapshot grain.
-- Deliverable mode: internal_analysis. All output is aggregate-only.
-- Population: worker_type = 'Employee', employee_type = 'Regular', active_status = 1.
-- Acceptance rule:
--   1) transaction_date = 2026-09-07 exists;
--   2) active regular employee-day rows equal distinct employees (no duplicates);
--   3) job_family is observable for the published population;
--   4) exactly 20 detailed families have n >= 30; and
--   5) Top 20 plus Other job families reconciles to observable employees.
WITH base AS (
  SELECT
    CAST(transaction_date AS DATE) AS snapshot_date,
    employee_id,
    NULLIF(TRIM(CAST(job_family AS VARCHAR(512))), '') AS job_family
  FROM hrda.post_hire_daily_worker_dtls
  WHERE CAST(transaction_date AS DATE) = DATE '2026-09-07'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
summary AS (
  SELECT
    snapshot_date,
    COUNT(*) AS active_regular_employee_day_rows,
    COUNT(DISTINCT employee_id) AS eligible_employees,
    COUNT(DISTINCT CASE WHEN job_family IS NOT NULL THEN employee_id END) AS observable_employees,
    COUNT(DISTINCT job_family) AS detailed_family_count
  FROM base
  GROUP BY 1
),
family_counts AS (
  SELECT
    snapshot_date,
    job_family,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM base
  WHERE job_family IS NOT NULL
  GROUP BY 1, 2
),
ranked_families AS (
  SELECT
    snapshot_date,
    job_family,
    employee_count,
    ROW_NUMBER() OVER (
      PARTITION BY snapshot_date
      ORDER BY employee_count DESC, job_family
    ) AS category_rank
  FROM family_counts
),
top_20 AS (
  SELECT
    snapshot_date,
    job_family,
    employee_count,
    category_rank
  FROM ranked_families
  WHERE category_rank <= 20
    AND employee_count >= 30
),
top_20_totals AS (
  SELECT
    snapshot_date,
    COUNT(*) AS top_20_category_count,
    SUM(employee_count) AS top_20_employee_count,
    MIN(employee_count) AS top_20_min_employee_count
  FROM top_20
  GROUP BY 1
)
SELECT
  'snapshot_summary' AS row_type,
  summary.snapshot_date,
  CAST(NULL AS INTEGER) AS category_rank,
  CAST(NULL AS VARCHAR(512)) AS category_label,
  CAST(NULL AS BIGINT) AS employee_count,
  summary.active_regular_employee_day_rows,
  summary.eligible_employees,
  summary.observable_employees,
  summary.detailed_family_count,
  top_20_totals.top_20_category_count,
  top_20_totals.top_20_employee_count,
  summary.observable_employees - top_20_totals.top_20_employee_count AS other_job_families_employee_count,
  top_20_totals.top_20_min_employee_count
FROM summary
INNER JOIN top_20_totals
  ON top_20_totals.snapshot_date = summary.snapshot_date

UNION ALL

SELECT
  'top_20_job_family' AS row_type,
  top_20.snapshot_date,
  top_20.category_rank,
  top_20.job_family AS category_label,
  top_20.employee_count,
  CAST(NULL AS BIGINT) AS active_regular_employee_day_rows,
  CAST(NULL AS BIGINT) AS eligible_employees,
  CAST(NULL AS BIGINT) AS observable_employees,
  CAST(NULL AS BIGINT) AS detailed_family_count,
  CAST(NULL AS BIGINT) AS top_20_category_count,
  CAST(NULL AS BIGINT) AS top_20_employee_count,
  CAST(NULL AS BIGINT) AS other_job_families_employee_count,
  CAST(NULL AS BIGINT) AS top_20_min_employee_count
FROM top_20
ORDER BY snapshot_date, row_type, category_rank;
