/*
  Attrition model preflight: target horizon comparison.

  Claim:
    A time-safe voluntary attrition target can be measured from monthly active
    employee snapshots at several candidate horizons.

  Population:
    worker_type = 'Employee', employee_type = 'Regular', active_status = 1.

  Grain:
    One employee-snapshot. A positive target means at least one deduplicated
    Voluntary termination event occurs after the snapshot and on or before the
    selected horizon boundary.

  Acceptance rule:
    Prefer a horizon with at least 24 complete snapshot months and enough
    positive events for temporal validation. The output reports the metrics
    needed for that decision; it does not select a horizon automatically.

  Leakage control:
    The target is joined only to term_date values strictly after the snapshot.
    Snapshots whose follow-up extends beyond the source's latest snapshot are
    excluded from the horizon-specific denominator.

  Privacy:
    employee_id is used only for internal joins, deduplication and counts.
    Results are aggregate only.
*/
WITH source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
),
horizons AS (
  SELECT 1 AS horizon_months
  UNION ALL SELECT 3
  UNION ALL SELECT 6
  UNION ALL SELECT 12
),
active_snapshots AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY 1, 2
),
eligible_snapshots AS (
  SELECT
    h.horizon_months,
    a.snapshot_date,
    a.employee_id
  FROM horizons h
  CROSS JOIN source_bounds b
  JOIN active_snapshots a
    ON a.snapshot_date <= DATEADD(month, -h.horizon_months, b.latest_snapshot_date)
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
    e.horizon_months,
    e.snapshot_date,
    e.employee_id,
    MAX(
      CASE
        WHEN v.employee_id IS NOT NULL THEN 1
        ELSE 0
      END
    ) AS voluntary_attrition_target
  FROM eligible_snapshots e
  LEFT JOIN voluntary_events v
    ON v.employee_id = e.employee_id
   AND v.term_date > e.snapshot_date
   AND v.term_date <= DATEADD(month, e.horizon_months, e.snapshot_date)
  GROUP BY 1, 2, 3
),
monthly_metrics AS (
  SELECT
    horizon_months,
    snapshot_date,
    COUNT(*) AS eligible_employee_snapshots,
    SUM(voluntary_attrition_target) AS positive_employee_snapshots,
    100.0 * SUM(voluntary_attrition_target)
      / NULLIF(COUNT(*), 0) AS monthly_target_rate_percent
  FROM target_flags
  GROUP BY 1, 2
)
SELECT
  horizon_months,
  COUNT(*) AS complete_snapshot_months,
  MIN(snapshot_date) AS first_complete_snapshot,
  MAX(snapshot_date) AS last_complete_snapshot,
  SUM(eligible_employee_snapshots) AS eligible_employee_snapshots,
  SUM(positive_employee_snapshots) AS positive_employee_snapshots,
  ROUND(
    100.0 * SUM(positive_employee_snapshots)
      / NULLIF(SUM(eligible_employee_snapshots), 0),
    4
  ) AS target_rate_percent,
  ROUND(MIN(monthly_target_rate_percent), 4)
    AS minimum_monthly_target_rate_percent,
  ROUND(MAX(monthly_target_rate_percent), 4)
    AS maximum_monthly_target_rate_percent,
  SUM(
    CASE WHEN positive_employee_snapshots >= 30 THEN 1 ELSE 0 END
  ) AS months_with_at_least_30_positive_events,
  CASE
    WHEN COUNT(*) >= 24
     AND SUM(positive_employee_snapshots) >= 30
    THEN 'pass'
    ELSE 'review'
  END AS temporal_measurement_outcome
FROM monthly_metrics
GROUP BY 1
ORDER BY horizon_months;
