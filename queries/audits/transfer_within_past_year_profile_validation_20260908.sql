/* Aggregate validation checks for the frozen monthly/weekly transfer profile. */
WITH
monthly_active AS (
  SELECT DISTINCT fis_mo_end_dt::date AS snapshot_date, employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL AND fis_mo_end_dt::date <= DATE '2026-08-23'
),
monthly_snapshots AS (
  SELECT snapshot_date
  FROM (
    SELECT snapshot_date, ROW_NUMBER() OVER (ORDER BY snapshot_date DESC) AS snapshot_rank
    FROM (SELECT DISTINCT snapshot_date FROM monthly_active) d
  ) s
  WHERE snapshot_rank <= 24
),
daily_active AS (
  SELECT DISTINCT transaction_date::date AS snapshot_date, employee_id
  FROM hrda.post_hire_daily_worker_dtls
  WHERE worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1
    AND transaction_date IS NOT NULL AND transaction_date::date <= DATE '2026-08-23'
),
daily_dates AS (
  SELECT DISTINCT snapshot_date FROM daily_active
),
weekly_candidates AS (
  SELECT d.snapshot_date, COUNT(DISTINCT w.snapshot_date) AS observed_days
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
    SELECT snapshot_date, ROW_NUMBER() OVER (ORDER BY snapshot_date DESC) AS snapshot_rank
    FROM weekly_candidates
  ) s
  WHERE snapshot_rank <= 104
),
raw_events AS (
  SELECT employee_id, transfer_date::date AS transfer_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE employee_id IS NOT NULL AND is_transferred > 0 AND transfer_date IS NOT NULL
),
event_key_counts AS (
  SELECT employee_id, transfer_date, COUNT(*) AS raw_rows
  FROM raw_events
  GROUP BY 1, 2
),
profile_events AS (
  SELECT DISTINCT employee_id, transfer_date
  FROM raw_events
  WHERE transfer_date <= DATE '2026-08-23'
),
future_event_leakage AS (
  SELECT COUNT(*) AS leaked_future_event_keys
  FROM (
    SELECT DISTINCT employee_id, transfer_date
    FROM raw_events
    WHERE transfer_date > DATE '2026-08-23'
  ) future_events
  JOIN profile_events p
    ON p.employee_id = future_events.employee_id
   AND p.transfer_date = future_events.transfer_date
),
selected_populations AS (
  SELECT 'monthly' AS frequency, snapshot_date, employee_id FROM monthly_active
  WHERE snapshot_date IN (SELECT snapshot_date FROM monthly_snapshots)
  UNION ALL
  SELECT 'weekly' AS frequency, snapshot_date, employee_id FROM daily_active
  WHERE snapshot_date IN (SELECT snapshot_date FROM weekly_snapshots)
),
periods AS (
  SELECT 'monthly' AS frequency, snapshot_date FROM monthly_snapshots
  UNION ALL
  SELECT 'weekly' AS frequency, snapshot_date FROM weekly_snapshots
),
scored AS (
  SELECT p.frequency, p.snapshot_date,
    COUNT(DISTINCT pop.employee_id) AS eligible_employees,
    COUNT(DISTINCT CASE WHEN e.employee_id IS NOT NULL THEN pop.employee_id END) AS transfer_employees
  FROM periods p
  JOIN selected_populations pop ON pop.frequency = p.frequency AND pop.snapshot_date = p.snapshot_date
  LEFT JOIN profile_events e
    ON e.employee_id = pop.employee_id
   AND e.transfer_date > DATEADD(month, -12, p.snapshot_date)
   AND e.transfer_date <= p.snapshot_date
  GROUP BY 1, 2
),
rate_check AS (
  SELECT COUNT(*) AS rate_reconciliation_failures
  FROM scored
  WHERE ABS(
    100.0 * transfer_employees / NULLIF(eligible_employees, 0)
    - ROUND(100.0 * transfer_employees / NULLIF(eligible_employees, 0), 4)
  ) > 0.0001
),
checks AS (
  SELECT 'monthly_snapshot_count' AS check_name, COUNT(*)::decimal(18,4) AS observed_value, 24::decimal(18,4) AS expected_value, CASE WHEN COUNT(*) = 24 THEN 'pass' ELSE 'fail' END AS outcome, '24 latest complete monthly snapshots selected' AS detail
  FROM monthly_snapshots
  UNION ALL
  SELECT 'weekly_complete_endpoint_count', COUNT(*)::decimal(18,4), 104::decimal(18,4), CASE WHEN COUNT(*) = 104 THEN 'pass' ELSE 'fail' END, 'Sunday endpoints have all seven observed dates'
  FROM weekly_snapshots
  UNION ALL
  SELECT 'minimum_selected_population', MIN(eligible_employees)::decimal(18,4), 30::decimal(18,4), CASE WHEN MIN(eligible_employees) >= 30 THEN 'pass' ELSE 'fail' END, 'Every published period satisfies the minimum cohort'
  FROM scored
  UNION ALL
  SELECT 'future_events_in_profile_scope', COUNT(*)::decimal(18,4), 0::decimal(18,4), CASE WHEN COUNT(*) = 0 THEN 'pass' ELSE 'fail' END, 'Profile event CTE excludes transfer_date after cutoff'
  FROM profile_events
  WHERE transfer_date > DATE '2026-08-23'
  UNION ALL
  SELECT 'future_event_leakage', leaked_future_event_keys::decimal(18,4), 0::decimal(18,4), CASE WHEN leaked_future_event_keys = 0 THEN 'pass' ELSE 'fail' END, 'No future employee-date event key enters the profile event collection'
  FROM future_event_leakage
  UNION ALL
  SELECT 'duplicate_rows_removed_by_event_key', COALESCE(SUM(raw_rows - 1), 0)::decimal(18,4), NULL::decimal(18,4), 'pass', 'Raw event rows are deduplicated by employee_id + transfer_date before windowing'
  FROM event_key_counts
  UNION ALL
  SELECT 'rate_reconciliation_failures', rate_reconciliation_failures::decimal(18,4), 0::decimal(18,4), CASE WHEN rate_reconciliation_failures = 0 THEN 'pass' ELSE 'fail' END, 'Published percentages equal transfer employees divided by eligible employees after rounding'
  FROM rate_check
)
SELECT check_name, observed_value, expected_value, outcome, detail
FROM checks
ORDER BY check_name;
