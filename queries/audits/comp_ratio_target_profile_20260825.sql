WITH eligible AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    compa_ratio
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
    AND fis_mo_end_dt <= DATE '2026-08-25'
), grain AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    COUNT(*) AS rows_at_grain
  FROM eligible
  GROUP BY employee_id, fis_mo_end_dt
), metrics AS (
  SELECT
    COUNT(*) AS eligible_rows,
    COUNT(DISTINCT employee_id) AS eligible_employees,
    COUNT(DISTINCT fis_mo_end_dt) AS snapshot_dates,
    COUNT(DISTINCT CASE WHEN compa_ratio IS NOT NULL THEN employee_id END) AS populated_employees,
    SUM(CASE WHEN compa_ratio IS NOT NULL THEN 1 ELSE 0 END) AS populated_rows,
    SUM(CASE WHEN compa_ratio IS NULL THEN 1 ELSE 0 END) AS missing_rows,
    SUM(CASE WHEN compa_ratio IS NOT NULL AND compa_ratio <= 0 THEN 1 ELSE 0 END) AS nonpositive_rows,
    SUM(CASE WHEN compa_ratio > 3 THEN 1 ELSE 0 END) AS above_three_rows,
    SUM(CASE WHEN compa_ratio > 0 AND compa_ratio <= 3 THEN 1 ELSE 0 END) AS positive_rows,
    MIN(fis_mo_end_dt) AS first_snapshot_date,
    MAX(fis_mo_end_dt) AS latest_snapshot_date
  FROM eligible
), grain_metrics AS (
  SELECT
    COUNT(*) AS employee_snapshot_groups,
    SUM(CASE WHEN rows_at_grain = 1 THEN 1 ELSE 0 END) AS unique_employee_snapshot_groups,
    SUM(CASE WHEN rows_at_grain > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_groups,
    SUM(CASE WHEN rows_at_grain > 1 THEN rows_at_grain ELSE 0 END) AS rows_in_duplicate_groups
  FROM grain
)
SELECT
  metrics.eligible_rows,
  metrics.eligible_employees,
  metrics.snapshot_dates,
  metrics.populated_employees,
  metrics.populated_rows,
  metrics.missing_rows,
  metrics.nonpositive_rows,
  metrics.above_three_rows,
  metrics.positive_rows,
  metrics.first_snapshot_date,
  metrics.latest_snapshot_date,
  grain_metrics.employee_snapshot_groups,
  grain_metrics.unique_employee_snapshot_groups,
  grain_metrics.duplicate_employee_snapshot_groups,
  grain_metrics.rows_in_duplicate_groups,
  ROUND(100.0 * metrics.populated_rows / NULLIF(metrics.eligible_rows, 0), 2) AS populated_row_rate_percent,
  ROUND(100.0 * metrics.populated_employees / NULLIF(metrics.eligible_employees, 0), 2) AS populated_employee_rate_percent
FROM metrics
CROSS JOIN grain_metrics
WHERE metrics.eligible_employees >= 30;
