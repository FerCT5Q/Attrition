-- Aggregate-only domain and history audit for work_arrangement. Categories are
-- non-sensitive operational labels and are shown only for cohorts >= 30.
-- It tests whether the stored domain is actually limited to the requested
-- Remote / Hybrid / In-office concepts or needs an explicit business mapping.

WITH base AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    UPPER(NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), ''))
      AS normalized_work_arrangement,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
latest_snapshot AS (
  SELECT MAX(snapshot_date) AS snapshot_date
  FROM base
),
history AS (
  SELECT
    normalized_work_arrangement,
    COUNT(DISTINCT b.snapshot_date) AS observed_months,
    MIN(b.snapshot_date) AS first_seen_snapshot_date,
    MAX(b.snapshot_date) AS last_seen_snapshot_date,
    COUNT(DISTINCT b.employee_id) AS distinct_employees_observed,
    SUM(CASE WHEN b.snapshot_date = l.snapshot_date THEN 1 ELSE 0 END)
      AS latest_snapshot_rows
  FROM base b
  CROSS JOIN latest_snapshot l
  WHERE normalized_work_arrangement IS NOT NULL
  GROUP BY normalized_work_arrangement
)
SELECT
  normalized_work_arrangement,
  observed_months,
  first_seen_snapshot_date,
  last_seen_snapshot_date,
  distinct_employees_observed,
  latest_snapshot_rows
FROM history
WHERE distinct_employees_observed >= 30
ORDER BY latest_snapshot_rows DESC, distinct_employees_observed DESC,
  normalized_work_arrangement;
