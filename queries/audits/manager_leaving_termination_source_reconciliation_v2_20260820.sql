WITH target_population AS (
  SELECT
    employee_id,
    CAST(manager_employee_id AS BIGINT) AS manager_id,
    fis_mo_end_dt AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
), history_bounds AS (
  SELECT MIN(snapshot_date) AS history_start_date, MAX(snapshot_date) AS history_end_date
  FROM target_population
), target_managers AS (
  SELECT DISTINCT manager_id
  FROM target_population
  WHERE manager_id IS NOT NULL
), all_termination_rows AS (
  SELECT
    a.employeeid AS manager_id,
    a.term_date,
    a.term_type
  FROM hrda.all_terminations a
  INNER JOIN target_managers tm
    ON tm.manager_id = a.employeeid
), all_termination_quality AS (
  SELECT
    COUNT(*) AS observations_checked,
    COUNT(DISTINCT DATE_TRUNC('month', term_date)) AS months_checked,
    SUM(CASE WHEN term_date IS NULL THEN 1 ELSE 0 END) AS null_term_date_rows
  FROM all_termination_rows
), all_event_rollup AS (
  SELECT
    a.manager_id,
    a.term_date,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT a.term_type) AS distinct_term_types
  FROM all_termination_rows a
  CROSS JOIN history_bounds h
  WHERE a.term_date IS NOT NULL
    AND a.term_date BETWEEN h.history_start_date AND h.history_end_date
  GROUP BY 1, 2
), all_events AS (
  SELECT manager_id, term_date
  FROM all_event_rollup
), term_table_rows AS (
  SELECT
    t.employee_id AS manager_id,
    t.term_date,
    t.term_type,
    t.is_termed
  FROM hrda.post_hire_monthly_worker_dtls_term t
  INNER JOIN target_managers tm
    ON tm.manager_id = t.employee_id
), term_table_quality AS (
  SELECT
    COUNT(*) AS term_table_rows_checked,
    SUM(CASE WHEN is_termed IS NOT NULL AND is_termed NOT IN (0, 1) THEN 1 ELSE 0 END) AS invalid_flag_rows,
    SUM(CASE WHEN COALESCE(is_termed, 0) = 1 AND term_date IS NULL THEN 1 ELSE 0 END) AS flagged_without_date_rows
  FROM term_table_rows
), term_table_event_rollup AS (
  SELECT
    t.manager_id,
    t.term_date,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT t.term_type) AS distinct_term_types
  FROM term_table_rows t
  CROSS JOIN history_bounds h
  WHERE COALESCE(t.is_termed, 0) = 1
    AND t.term_date IS NOT NULL
    AND t.term_date BETWEEN h.history_start_date AND h.history_end_date
  GROUP BY 1, 2
), term_table_events AS (
  SELECT manager_id, term_date
  FROM term_table_event_rollup
), event_comparison AS (
  SELECT
    COALESCE(a.manager_id, t.manager_id) AS manager_id,
    COALESCE(a.term_date, t.term_date) AS term_date,
    CASE WHEN a.manager_id IS NOT NULL THEN 1 ELSE 0 END AS in_all_terminations,
    CASE WHEN t.manager_id IS NOT NULL THEN 1 ELSE 0 END AS in_term_table
  FROM all_events a
  FULL OUTER JOIN term_table_events t
    ON t.manager_id = a.manager_id
   AND t.term_date = a.term_date
), reconciliation AS (
  SELECT
    COUNT(*) AS comparable_event_count,
    SUM(CASE WHEN in_all_terminations = 1 AND in_term_table = 1 THEN 1 ELSE 0 END) AS matched_event_count,
    SUM(CASE WHEN in_all_terminations = 1 AND in_term_table = 0 THEN 1 ELSE 0 END) AS all_terminations_only_event_count,
    SUM(CASE WHEN in_all_terminations = 0 AND in_term_table = 1 THEN 1 ELSE 0 END) AS term_table_only_event_count
  FROM event_comparison
), all_event_quality AS (
  SELECT
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS duplicate_event_rows,
    COALESCE(SUM(CASE WHEN distinct_term_types > 1 THEN 1 ELSE 0 END), 0) AS term_type_conflict_event_count
  FROM all_event_rollup
), term_event_quality AS (
  SELECT
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS term_table_duplicate_event_rows,
    COALESCE(SUM(CASE WHEN distinct_term_types > 1 THEN 1 ELSE 0 END), 0) AS term_table_term_type_conflict_event_count
  FROM term_table_event_rollup
)
SELECT
  'Manager leaving' AS variable_name,
  a.observations_checked,
  a.months_checked,
  a.null_term_date_rows,
  t.term_table_rows_checked,
  t.invalid_flag_rows,
  t.flagged_without_date_rows,
  r.comparable_event_count,
  r.matched_event_count,
  r.all_terminations_only_event_count,
  r.term_table_only_event_count,
  q.duplicate_event_rows,
  q.term_type_conflict_event_count,
  u.term_table_duplicate_event_rows,
  u.term_table_term_type_conflict_event_count,
  (
    a.null_term_date_rows
    + t.invalid_flag_rows
    + t.flagged_without_date_rows
    + r.all_terminations_only_event_count
    + r.term_table_only_event_count
    + q.term_type_conflict_event_count
    + u.term_table_term_type_conflict_event_count
  ) AS anomaly_count,
  (
    a.null_term_date_rows
    + t.invalid_flag_rows
    + t.flagged_without_date_rows
  ) AS invalid_count,
  (
    r.all_terminations_only_event_count
    + r.term_table_only_event_count
    + q.term_type_conflict_event_count
    + u.term_table_term_type_conflict_event_count
  ) AS unexplained_change_count
FROM all_termination_quality a
CROSS JOIN term_table_quality t
CROSS JOIN reconciliation r
CROSS JOIN all_event_quality q
CROSS JOIN term_event_quality u;

