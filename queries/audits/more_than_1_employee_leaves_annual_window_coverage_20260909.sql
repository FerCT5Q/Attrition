-- Purpose: measure whether the 40 six-month evaluation snapshots also have
-- twelve distinct monthly snapshots in their trailing calendar-year window.
-- Aggregate-only; no employee or manager identifiers are returned.

WITH
parameters AS (
  SELECT DATE '2026-08-23' AS cutoff_date
),
snapshot_dates AS (
  SELECT CAST(worker.fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls AS worker
  CROSS JOIN parameters
  WHERE CAST(worker.fis_mo_end_dt AS DATE) <= parameters.cutoff_date
    AND worker.worker_type = 'Employee'
    AND worker.employee_type = 'Regular'
    AND worker.active_status = 1
  GROUP BY 1
),
six_month_evaluation_snapshots AS (
  SELECT
    evaluation.snapshot_date,
    COUNT(DISTINCT history.snapshot_date) AS six_month_snapshot_count
  FROM snapshot_dates AS evaluation
  LEFT JOIN snapshot_dates AS history
    ON history.snapshot_date > DATEADD(month, -6, evaluation.snapshot_date)
   AND history.snapshot_date <= evaluation.snapshot_date
  GROUP BY 1
  HAVING COUNT(DISTINCT history.snapshot_date) = 6
),
annual_coverage AS (
  SELECT
    evaluation.snapshot_date,
    COUNT(DISTINCT history.snapshot_date) AS annual_snapshot_count,
    MIN(history.snapshot_date) AS earliest_snapshot_in_window,
    MAX(history.snapshot_date) AS latest_snapshot_in_window
  FROM six_month_evaluation_snapshots AS evaluation
  LEFT JOIN snapshot_dates AS history
    ON history.snapshot_date > DATEADD(month, -12, evaluation.snapshot_date)
   AND history.snapshot_date <= evaluation.snapshot_date
  GROUP BY 1
)
SELECT
  snapshot_date,
  annual_snapshot_count,
  earliest_snapshot_in_window,
  latest_snapshot_in_window,
  DATEDIFF(day, earliest_snapshot_in_window, latest_snapshot_in_window) AS observed_span_days,
  CASE
    WHEN annual_snapshot_count >= 12 AND DATEDIFF(day, earliest_snapshot_in_window, latest_snapshot_in_window) >= 330
    THEN 1
    ELSE 0
  END AS has_complete_annual_window
FROM annual_coverage
ORDER BY snapshot_date;
