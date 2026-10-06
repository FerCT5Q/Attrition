/*
  Transfer within past year: comparable monthly and weekly snapshots.

  Deliverable: presentation.  This query returns aggregate-only rows with
  cohorts >= 30.  The feature is defined as distinct employees with at least
  one documented transfer event in (snapshot_date - 12 months, snapshot_date].
  Monthly is the canonical employee-snapshot grain; weekly is an operational
  comparison using daily transaction_date endpoints.

  Cutoff: 2026-08-23.  Monthly: 24 latest fiscal-month-end snapshots (about two
  years).  Weekly: 104 latest Sunday endpoints with all seven transaction dates
  present (about two years).
*/
WITH
monthly_active AS (
  SELECT DISTINCT
    fis_mo_end_dt::date AS snapshot_date,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
    AND fis_mo_end_dt::date <= DATE '2026-08-23'
),
monthly_snapshots AS (
  SELECT snapshot_date
  FROM (
    SELECT snapshot_date,
      ROW_NUMBER() OVER (ORDER BY snapshot_date DESC) AS snapshot_rank
    FROM (SELECT DISTINCT snapshot_date FROM monthly_active) d
  ) s
  WHERE snapshot_rank <= 24
),
daily_active AS (
  SELECT DISTINCT
    transaction_date::date AS snapshot_date,
    employee_id
  FROM hrda.post_hire_daily_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND transaction_date IS NOT NULL
    AND transaction_date::date <= DATE '2026-08-23'
),
daily_dates AS (
  SELECT DISTINCT snapshot_date
  FROM daily_active
),
weekly_candidates AS (
  SELECT
    d.snapshot_date,
    COUNT(DISTINCT w.snapshot_date) AS observed_days
  FROM daily_dates d
  LEFT JOIN daily_dates w
    ON w.snapshot_date BETWEEN DATEADD(day, -6, d.snapshot_date) AND d.snapshot_date
  WHERE DATE_PART(dow, d.snapshot_date) = 0
  GROUP BY d.snapshot_date
  HAVING COUNT(DISTINCT w.snapshot_date) = 7
),
weekly_snapshots AS (
  SELECT snapshot_date
  FROM (
    SELECT snapshot_date,
      ROW_NUMBER() OVER (ORDER BY snapshot_date DESC) AS snapshot_rank
    FROM weekly_candidates
  ) s
  WHERE snapshot_rank <= 104
),
transfer_events AS (
  SELECT DISTINCT
    employee_id,
    transfer_date::date AS transfer_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE employee_id IS NOT NULL
    AND is_transferred > 0
    AND transfer_date IS NOT NULL
    AND transfer_date::date <= DATE '2026-08-23'
),
periods AS (
  SELECT 'monthly' AS frequency, snapshot_date, TRUE AS period_complete
  FROM monthly_snapshots
  UNION ALL
  SELECT 'weekly' AS frequency, snapshot_date, TRUE AS period_complete
  FROM weekly_snapshots
),
populations AS (
  SELECT 'monthly' AS frequency, snapshot_date, employee_id
  FROM monthly_active
  WHERE snapshot_date IN (SELECT snapshot_date FROM monthly_snapshots)
  UNION ALL
  SELECT 'weekly' AS frequency, snapshot_date, employee_id
  FROM daily_active
  WHERE snapshot_date IN (SELECT snapshot_date FROM weekly_snapshots)
),
scored AS (
  SELECT
    p.frequency,
    p.snapshot_date,
    p.period_complete,
    COUNT(DISTINCT pop.employee_id) AS eligible_employees,
    COUNT(DISTINCT CASE WHEN e.employee_id IS NOT NULL THEN pop.employee_id END) AS transfer_employees,
    COUNT(DISTINCT e.transfer_date) AS transfer_events_in_window,
    ROUND(
      100.0 * COUNT(DISTINCT CASE WHEN e.employee_id IS NOT NULL THEN pop.employee_id END)
      / NULLIF(COUNT(DISTINCT pop.employee_id), 0),
      4
    ) AS transfer_rate_percent
  FROM periods p
  JOIN populations pop
    ON pop.frequency = p.frequency
   AND pop.snapshot_date = p.snapshot_date
  LEFT JOIN transfer_events e
    ON e.employee_id = pop.employee_id
   AND e.transfer_date > DATEADD(month, -12, p.snapshot_date)
   AND e.transfer_date <= p.snapshot_date
  GROUP BY 1, 2, 3
)
SELECT
  frequency,
  snapshot_date,
  period_complete,
  eligible_employees,
  transfer_employees,
  transfer_events_in_window,
  transfer_rate_percent,
  CASE WHEN eligible_employees >= 30 THEN 'publish' ELSE 'suppress' END AS publication_status
FROM scored
WHERE eligible_employees >= 30
ORDER BY frequency, snapshot_date;
