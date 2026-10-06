-- Aggregate-only history audit for the stored work_arrangement field.
-- It counts usable monthly observations rather than elapsed calendar days.
-- A usable observation has >=95% raw-field coverage among active Regular
-- Employees. The result tests whether the monthly-model interpretation has at
-- least 24 usable snapshots.

WITH monthly AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    COUNT(DISTINCT employee_id) AS eligible_employees,
    COUNT(DISTINCT CASE
      WHEN NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '') IS NOT NULL
      THEN employee_id END
    ) AS observable_employees
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY CAST(fis_mo_end_dt AS DATE)
  HAVING COUNT(DISTINCT employee_id) >= 30
),
populated_months AS (
  SELECT
    snapshot_date,
    eligible_employees,
    observable_employees,
    100.0 * observable_employees / NULLIF(eligible_employees, 0) AS coverage_percent
  FROM monthly
  WHERE observable_employees > 0
)
SELECT
  MIN(snapshot_date) AS first_populated_snapshot_date,
  MAX(snapshot_date) AS latest_populated_snapshot_date,
  COUNT(*) AS populated_monthly_observations,
  SUM(CASE WHEN coverage_percent >= 95 THEN 1 ELSE 0 END)
    AS usable_monthly_observations_at_95_percent,
  SUM(CASE WHEN coverage_percent < 95 THEN 1 ELSE 0 END)
    AS populated_observations_below_95_percent,
  ROUND(MIN(coverage_percent), 4) AS minimum_populated_month_coverage_percent,
  ROUND(MAX(coverage_percent), 4) AS maximum_populated_month_coverage_percent
FROM populated_months;
