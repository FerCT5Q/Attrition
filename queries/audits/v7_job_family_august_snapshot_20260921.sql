/*
  Claim: the V7 Job family display uses the fiscal August 2026 monthly
  snapshot, not the special daily September reorganization snapshot.

  Internal analysis, aggregate-only. Top 20 detailed families plus Other must
  reconcile exactly to active Regular Employees with a nonblank job_family.
*/
WITH base AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(employee_id AS BIGINT) AS employee_id,
    NULLIF(TRIM(CAST(job_family AS VARCHAR(512))), '') AS job_family
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE '2026-08-23'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
),
snapshot_quality AS (
  SELECT
    snapshot_date,
    COUNT(*) AS active_regular_source_rows,
    COUNT(DISTINCT employee_id) AS active_regular_employees,
    COUNT(*) - COUNT(DISTINCT employee_id) AS duplicate_employee_rows,
    COUNT(DISTINCT CASE WHEN job_family IS NOT NULL THEN employee_id END) AS observable_employees
  FROM base
  GROUP BY 1
),
family_counts AS (
  SELECT snapshot_date, job_family, COUNT(DISTINCT employee_id) AS employee_count
  FROM base
  WHERE job_family IS NOT NULL
  GROUP BY 1, 2
),
ranked AS (
  SELECT
    snapshot_date,
    job_family,
    employee_count,
    ROW_NUMBER() OVER (PARTITION BY snapshot_date ORDER BY employee_count DESC, job_family) AS category_rank
  FROM family_counts
),
top_20 AS (
  SELECT snapshot_date, job_family, employee_count, category_rank
  FROM ranked
  WHERE category_rank <= 20
),
top_20_total AS (
  SELECT snapshot_date, COUNT(*) AS top_20_category_count, SUM(employee_count) AS top_20_employee_count, MIN(employee_count) AS top_20_min_employee_count
  FROM top_20
  GROUP BY 1
)
SELECT
  'summary' AS row_type,
  quality.snapshot_date,
  CAST(NULL AS INTEGER) AS category_rank,
  CAST(NULL AS VARCHAR(512)) AS category_label,
  CAST(NULL AS BIGINT) AS employee_count,
  quality.active_regular_source_rows,
  quality.active_regular_employees,
  quality.observable_employees,
  quality.duplicate_employee_rows,
  total.top_20_category_count,
  total.top_20_employee_count,
  quality.observable_employees - total.top_20_employee_count AS other_job_families_employee_count,
  total.top_20_min_employee_count
FROM snapshot_quality AS quality
INNER JOIN top_20_total AS total
  ON total.snapshot_date = quality.snapshot_date
UNION ALL
SELECT
  'top_20' AS row_type,
  snapshot_date,
  category_rank,
  job_family AS category_label,
  employee_count,
  CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT)
FROM top_20
ORDER BY row_type, category_rank;
