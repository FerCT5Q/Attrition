/*
  Attrition model preflight: exact next-snapshot hazard prevalence.

  Claim:
    A monthly discrete-time hazard target can be defined without overlapping
    outcome windows by using the actual next workforce snapshot date.

  Population:
    worker_type = 'Employee', employee_type = 'Regular', active_status = 1.

  Grain:
    One employee-snapshot interval from snapshot_date (exclusive) to
    next_snapshot_date (inclusive).

  Acceptance rule:
    At least 24 complete snapshot intervals and at least 30 positive events,
    with all target dates after the prediction snapshot and no interval ending
    after the execution-date knowledge boundary.

  Privacy:
    employee_id is used only for internal joins, deduplication and counts.
*/
WITH snapshot_calendar AS (
  SELECT
    snapshot_date,
    LEAD(snapshot_date) OVER (ORDER BY snapshot_date) AS next_snapshot_date
  FROM (
    SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
      AND CAST(fis_mo_end_dt AS DATE) <= DATE '2026-09-07'
  ) dates
),
active_snapshots AS (
  SELECT
    c.snapshot_date,
    c.next_snapshot_date,
    w.employee_id
  FROM snapshot_calendar c
  JOIN hrda.post_hire_monthly_worker_dtls w
    ON CAST(w.fis_mo_end_dt AS DATE) = c.snapshot_date
  WHERE c.next_snapshot_date IS NOT NULL
    AND c.next_snapshot_date <= DATE '2026-09-07'
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
  GROUP BY 1, 2, 3
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
target_flags AS (
  SELECT
    a.snapshot_date,
    a.next_snapshot_date,
    a.employee_id,
    MAX(
      CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END
    ) AS voluntary_next_snapshot
  FROM active_snapshots a
  LEFT JOIN voluntary_events v
    ON v.employee_id = a.employee_id
   AND v.term_date > a.snapshot_date
   AND v.term_date <= a.next_snapshot_date
  GROUP BY 1, 2, 3
),
monthly_metrics AS (
  SELECT
    snapshot_date,
    next_snapshot_date,
    COUNT(*) AS eligible_employee_snapshots,
    SUM(voluntary_next_snapshot) AS positive_employee_snapshots,
    100.0 * SUM(voluntary_next_snapshot)
      / NULLIF(COUNT(*), 0) AS monthly_hazard_rate_percent
  FROM target_flags
  GROUP BY 1, 2
)
SELECT
  COUNT(*) AS complete_snapshot_intervals,
  MIN(snapshot_date) AS first_snapshot,
  MAX(next_snapshot_date) AS last_next_snapshot,
  SUM(eligible_employee_snapshots) AS eligible_employee_snapshots,
  SUM(positive_employee_snapshots) AS positive_employee_snapshots,
  ROUND(
    100.0 * SUM(positive_employee_snapshots)
      / NULLIF(SUM(eligible_employee_snapshots), 0),
    4
  ) AS next_snapshot_hazard_rate_percent,
  ROUND(MIN(monthly_hazard_rate_percent), 4)
    AS minimum_monthly_hazard_rate_percent,
  ROUND(MAX(monthly_hazard_rate_percent), 4)
    AS maximum_monthly_hazard_rate_percent,
  SUM(CASE WHEN positive_employee_snapshots >= 30 THEN 1 ELSE 0 END)
    AS intervals_with_at_least_30_positive_events,
  CASE
    WHEN COUNT(*) >= 24
     AND SUM(positive_employee_snapshots) >= 30
    THEN 'pass'
    ELSE 'review'
  END AS hazard_measurement_outcome
FROM monthly_metrics;
