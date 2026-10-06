WITH target AS (
  SELECT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
), bounds AS (
  SELECT MIN(snapshot_date) AS min_snapshot_date, MAX(snapshot_date) AS max_snapshot_date
  FROM target
), employee_history AS (
  SELECT
    employee_id,
    MIN(snapshot_date) AS first_snapshot_date,
    MAX(snapshot_date) AS last_snapshot_date
  FROM target
  GROUP BY employee_id
), event_source AS (
  SELECT
    a.employeeid,
    a.term_date,
    a.max_hire_rehire_date
  FROM hrda.all_terminations a
  INNER JOIN employee_history h
    ON h.employee_id = a.employeeid
  CROSS JOIN bounds b
  WHERE a.term_date BETWEEN b.min_snapshot_date AND b.max_snapshot_date
    AND LOWER(TRIM(a.term_type)) IN ('voluntary', 'voluntary exception')
), events AS (
  SELECT
    employeeid,
    term_date,
    MAX(max_hire_rehire_date) AS max_hire_rehire_date
  FROM event_source
  GROUP BY employeeid, term_date
), event_history AS (
  SELECT
    e.employeeid,
    e.term_date,
    e.max_hire_rehire_date,
    h.first_snapshot_date,
    h.last_snapshot_date,
    MAX(CASE WHEN t.snapshot_date < e.term_date THEN t.snapshot_date END) AS last_prior_snapshot_date,
    MAX(CASE
      WHEN t.snapshot_date < e.term_date
       AND t.manager_employee_id IS NOT NULL
       AND DATEDIFF(day, t.snapshot_date, e.term_date) BETWEEN 0 AND 45
      THEN 1 ELSE 0 END) AS has_recent_manager_snapshot
  FROM events e
  INNER JOIN employee_history h
    ON h.employee_id = e.employeeid
  LEFT JOIN target t
    ON t.employee_id = e.employeeid
  GROUP BY
    e.employeeid,
    e.term_date,
    e.max_hire_rehire_date,
    h.first_snapshot_date,
    h.last_snapshot_date
), excluded AS (
  SELECT
    employeeid,
    term_date,
    max_hire_rehire_date,
    first_snapshot_date,
    last_snapshot_date,
    last_prior_snapshot_date,
    CASE
      WHEN last_prior_snapshot_date IS NULL AND term_date <= first_snapshot_date
        THEN 'event_before_first_target_snapshot'
      WHEN last_prior_snapshot_date IS NOT NULL AND term_date > last_snapshot_date
        THEN 'event_after_last_target_snapshot'
      WHEN last_prior_snapshot_date IS NOT NULL
       AND term_date BETWEEN first_snapshot_date AND last_snapshot_date
       AND DATEDIFF(day, last_prior_snapshot_date, term_date) > 45
        THEN 'gap_inside_target_history'
      ELSE 'unclassified'
    END AS exclusion_class
  FROM event_history
  WHERE has_recent_manager_snapshot = 0
), metrics AS (
  SELECT
    COUNT(*) AS excluded_event_count,
    COALESCE(SUM(CASE WHEN exclusion_class <> 'unclassified' THEN 1 ELSE 0 END), 0) AS classified_excluded_count,
    COALESCE(SUM(CASE WHEN exclusion_class = 'unclassified' THEN 1 ELSE 0 END), 0) AS unclassified_excluded_count,
    COALESCE(SUM(CASE WHEN exclusion_class = 'event_before_first_target_snapshot' THEN 1 ELSE 0 END), 0) AS event_before_first_target_snapshot_count,
    COALESCE(SUM(CASE WHEN exclusion_class = 'event_after_last_target_snapshot' THEN 1 ELSE 0 END), 0) AS event_after_last_target_snapshot_count,
    COALESCE(SUM(CASE WHEN exclusion_class = 'gap_inside_target_history' THEN 1 ELSE 0 END), 0) AS gap_inside_target_history_count,
    COALESCE(SUM(CASE WHEN max_hire_rehire_date > term_date THEN 1 ELSE 0 END), 0) AS term_before_latest_hire_count,
    COALESCE(SUM(CASE
      WHEN last_prior_snapshot_date IS NOT NULL
       AND DATEDIFF(day, last_prior_snapshot_date, term_date) BETWEEN 46 AND 90
      THEN 1 ELSE 0 END), 0) AS prior_lag_46_90_count,
    COALESCE(SUM(CASE
      WHEN last_prior_snapshot_date IS NOT NULL
       AND DATEDIFF(day, last_prior_snapshot_date, term_date) BETWEEN 91 AND 180
      THEN 1 ELSE 0 END), 0) AS prior_lag_91_180_count,
    COALESCE(SUM(CASE
      WHEN last_prior_snapshot_date IS NOT NULL
       AND DATEDIFF(day, last_prior_snapshot_date, term_date) > 180
      THEN 1 ELSE 0 END), 0) AS prior_lag_over_180_count
  FROM excluded
)
SELECT
  'High risk manager' AS variable_name,
  excluded_event_count,
  classified_excluded_count,
  unclassified_excluded_count,
  event_before_first_target_snapshot_count,
  event_after_last_target_snapshot_count,
  gap_inside_target_history_count,
  term_before_latest_hire_count,
  prior_lag_46_90_count,
  prior_lag_91_180_count,
  prior_lag_over_180_count
FROM metrics;
