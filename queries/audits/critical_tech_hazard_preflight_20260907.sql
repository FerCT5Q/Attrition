/*
  Critical Tech voluntary attrition hazard preflight.

  Claim:
    Critical Tech has enough temporal exposure and voluntary events to support
    a pooled monthly discrete-time hazard model and safe segment diagnostics.

  Population:
    worker_type='Employee', employee_type='Regular', active_status=1, with
    job_family matched to hrda.critical_tech.
  Grain:
    One employee-snapshot interval from snapshot_date (exclusive) through
    next_snapshot_date (inclusive).
  Knowledge boundary:
    Snapshot calendar and events are limited to 2026-09-07.
  Acceptance rule:
    A segment is eligible for an independent diagnostic only when it has at
    least 30 positive hazard intervals and at least 24 complete intervals.
    Smaller segments remain pooled and are not published separately.

  Privacy:
    Only aggregate segment results are returned. Positive counts below 30 are
    suppressed from the shared output.
*/
WITH critical_map AS (
  SELECT
    TRIM(LOWER(extended_job_family)) AS family_key,
    MAX(TRIM(seg)) AS seg
  FROM hrda.critical_tech
  GROUP BY 1
),
snapshot_calendar AS (
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
    p.employee_id,
    m.seg
  FROM snapshot_calendar c
  INNER JOIN hrda.post_hire_monthly_worker_dtls p
    ON CAST(p.fis_mo_end_dt AS DATE) = c.snapshot_date
  INNER JOIN critical_map m
    ON TRIM(LOWER(p.job_family)) = m.family_key
  WHERE c.next_snapshot_date IS NOT NULL
    AND c.next_snapshot_date <= DATE '2026-09-07'
    AND p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
  GROUP BY 1, 2, 3, 4
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
    a.seg,
    MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END)
      AS voluntary_next_snapshot
  FROM active_snapshots a
  LEFT JOIN voluntary_events v
    ON v.employee_id = a.employee_id
   AND v.term_date > a.snapshot_date
   AND v.term_date <= a.next_snapshot_date
  GROUP BY 1, 2, 3, 4
),
summary AS (
  SELECT
    seg,
    COUNT(*) AS employee_snapshot_intervals,
    COUNT(DISTINCT employee_id) AS distinct_employees,
    COUNT(DISTINCT snapshot_date) AS complete_snapshot_months,
    MIN(snapshot_date) AS first_snapshot,
    MAX(next_snapshot_date) AS last_next_snapshot,
    SUM(voluntary_next_snapshot) AS positive_hazard_intervals
  FROM target_flags
  GROUP BY 1
)
SELECT
  seg,
  employee_snapshot_intervals,
  distinct_employees,
  complete_snapshot_months,
  first_snapshot,
  last_next_snapshot,
  CASE WHEN positive_hazard_intervals >= 30
       THEN positive_hazard_intervals ELSE NULL END
    AS positive_hazard_intervals,
  CASE WHEN positive_hazard_intervals >= 30
       THEN ROUND(
         100.0 * positive_hazard_intervals
         / NULLIF(employee_snapshot_intervals, 0),
         4
       ) ELSE NULL END AS hazard_rate_percent,
  CASE WHEN positive_hazard_intervals >= 30
         AND complete_snapshot_months >= 24
       THEN 'pass'
       ELSE 'pooled_or_suppressed'
  END AS diagnostic_outcome
FROM summary
WHERE employee_snapshot_intervals >= 30
ORDER BY hazard_rate_percent DESC NULLS LAST, seg;
