/*
  Purpose: calculate the observed FY2026 voluntary-attrition rate for the
  Rehire (1) population shown in V7 slide 16.

  Deliverable: internal_analysis; aggregate-only.
  Claim: the label reports voluntary exits actually recorded during FY2026,
  divided by the average monthly active-Rehire headcount observed in the same
  fiscal-year window. It is a retrospective period rate, not the existing
  12-month prospective attrition target.
  Population: active Regular Employees at monthly snapshots
    (worker_type = 'Employee', employee_type = 'Regular', active_status = 1)
    where is_rehire = 1.
  Grain: employee-snapshot for exposure; distinct employee-term-date for exits.
  Event attribution: a voluntary termination belongs to Rehire only if the
    employee had an active Rehire snapshot strictly before its term date.

  Acceptance rule: publish only when the fiscal year has all 12 observed
  monthly snapshots, at least 30 Rehire employee-snapshot exposures, and at
  least 30 distinct Rehire employees. Display the observed end date and do not
  label the result as a prospective or post-snapshot 12-month rate.
*/
WITH fy_bounds AS (
  SELECT
    MIN(CAST(fis_mo_end_dt AS DATE)) AS first_snapshot_date,
    MAX(CAST(fis_mo_end_dt AS DATE)) AS last_snapshot_date,
    COUNT(DISTINCT CAST(fis_mo_end_dt AS DATE)) AS observed_snapshot_count
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fiscal_year = 2026
    AND fis_mo_end_dt IS NOT NULL
),
rehire_snapshots AS (
  SELECT
    CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
    w.employee_id,
    MAX(COALESCE(w.is_rehire, 0)) AS is_rehire
  FROM hrda.post_hire_monthly_worker_dtls w
  WHERE w.fiscal_year = 2026
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.fis_mo_end_dt IS NOT NULL
  GROUP BY 1, 2
),
rehire_exposure AS (
  SELECT snapshot_date, employee_id
  FROM rehire_snapshots
  WHERE is_rehire = 1
),
monthly_headcount AS (
  SELECT snapshot_date, COUNT(*) AS active_rehire_employee_count
  FROM rehire_exposure
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
rehire_voluntary_events AS (
  SELECT v.employee_id, v.term_date
  FROM voluntary_events v
  CROSS JOIN fy_bounds b
  WHERE v.term_date > b.first_snapshot_date
    AND v.term_date <= b.last_snapshot_date
    AND EXISTS (
      SELECT 1
      FROM rehire_exposure e
      WHERE e.employee_id = v.employee_id
        AND e.snapshot_date < v.term_date
    )
  GROUP BY 1, 2
),
exposure_aggregate AS (
  SELECT
    COUNT(*) AS employee_snapshot_count,
    COUNT(DISTINCT employee_id) AS distinct_employee_count
  FROM rehire_exposure
),
monthly_headcount_aggregate AS (
  SELECT AVG(active_rehire_employee_count) AS average_monthly_rehire_headcount
  FROM monthly_headcount
)
SELECT
  b.first_snapshot_date,
  b.last_snapshot_date,
  b.observed_snapshot_count,
  COALESCE(a.employee_snapshot_count, 0) AS employee_snapshot_count,
  COALESCE(a.distinct_employee_count, 0) AS distinct_employee_count,
  COALESCE(MAX(m.average_monthly_rehire_headcount), 0) AS average_monthly_rehire_headcount,
  COUNT(v.employee_id) AS voluntary_exit_count,
  CASE
    WHEN b.observed_snapshot_count >= 12
      AND COALESCE(a.employee_snapshot_count, 0) >= 30
      AND COALESCE(a.distinct_employee_count, 0) >= 30
      AND COALESCE(MAX(m.average_monthly_rehire_headcount), 0) > 0
    THEN 100.0 * COUNT(v.employee_id) / MAX(m.average_monthly_rehire_headcount)
    ELSE NULL
  END AS observed_voluntary_attrition_rate_percent,
  CASE
    WHEN b.observed_snapshot_count >= 12
      AND COALESCE(a.employee_snapshot_count, 0) >= 30
      AND COALESCE(a.distinct_employee_count, 0) >= 30
      AND COALESCE(MAX(m.average_monthly_rehire_headcount), 0) > 0
    THEN 'publishable_observed_period_rate'
    ELSE 'not_publishable_below_n30_or_no_observation'
  END AS publication_status
FROM fy_bounds b
LEFT JOIN exposure_aggregate a ON 1 = 1
LEFT JOIN monthly_headcount_aggregate m ON 1 = 1
LEFT JOIN rehire_voluntary_events v ON 1 = 1
GROUP BY 1, 2, 3, 4, 5
;
