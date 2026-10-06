WITH target_population AS (
  SELECT
    employee_id,
    manager_employee_id,
    manager_effective_date,
    fis_mo_beg_dt,
    fis_mo_end_dt
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
), history_bounds AS (
  SELECT
    MIN(fis_mo_beg_dt) AS history_start_date,
    MAX(fis_mo_end_dt) AS history_end_date
  FROM target_population
), target_managers AS (
  SELECT DISTINCT CAST(manager_employee_id AS BIGINT) AS manager_id
  FROM target_population
  WHERE manager_employee_id IS NOT NULL
), manager_monthly_rows AS (
  SELECT
    m.employee_id AS manager_id,
    m.fis_mo_beg_dt,
    m.fis_mo_end_dt,
    m.is_termed,
    m.term_date,
    m.term_type,
    m.max_hire_rehire_date
  FROM hrda.post_hire_monthly_worker_dtls m
  INNER JOIN target_managers tm
    ON tm.manager_id = m.employee_id
), monthly_row_quality AS (
  SELECT
    COUNT(*) AS observations_checked,
    COUNT(DISTINCT fis_mo_end_dt) AS months_checked,
    SUM(CASE WHEN is_termed IS NOT NULL AND is_termed NOT IN (0, 1) THEN 1 ELSE 0 END) AS invalid_flag_rows,
    SUM(CASE WHEN COALESCE(is_termed, 0) = 1 AND term_date IS NULL THEN 1 ELSE 0 END) AS flagged_without_date_rows,
    SUM(CASE WHEN COALESCE(is_termed, 0) = 1 AND term_date > fis_mo_end_dt THEN 1 ELSE 0 END) AS future_positive_flag_rows,
    SUM(
      CASE
        WHEN term_date IS NOT NULL
         AND term_date <= fis_mo_end_dt
         AND COALESCE(is_termed, 0) = 0
         AND (max_hire_rehire_date IS NULL OR term_date >= max_hire_rehire_date)
        THEN 1 ELSE 0
      END
    ) AS current_episode_date_without_positive_flag_rows,
    SUM(
      CASE
        WHEN COALESCE(is_termed, 0) = 1
         AND term_date IS NOT NULL
         AND max_hire_rehire_date IS NOT NULL
         AND term_date < max_hire_rehire_date
        THEN 1 ELSE 0
      END
    ) AS positive_flag_before_episode_start_rows,
    SUM(
      CASE
        WHEN term_date IS NOT NULL
         AND max_hire_rehire_date IS NOT NULL
         AND term_date < max_hire_rehire_date
        THEN 1 ELSE 0
      END
    ) AS historical_term_carried_into_rehire_rows
  FROM manager_monthly_rows
), relationship_row_quality AS (
  SELECT
    COUNT(*) AS relationship_rows_checked,
    SUM(CASE WHEN manager_effective_date > fis_mo_end_dt THEN 1 ELSE 0 END) AS future_manager_effective_date_rows,
    SUM(CASE WHEN manager_employee_id IS NOT NULL AND manager_effective_date IS NULL THEN 1 ELSE 0 END) AS missing_manager_effective_date_rows
  FROM target_population
), monthly_event_rollup AS (
  SELECT
    m.manager_id,
    m.term_date,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT m.term_type) AS distinct_term_types
  FROM manager_monthly_rows m
  CROSS JOIN history_bounds h
  WHERE COALESCE(m.is_termed, 0) = 1
    AND m.term_date IS NOT NULL
    AND m.term_date BETWEEN h.history_start_date AND h.history_end_date
  GROUP BY 1, 2
), monthly_events AS (
  SELECT manager_id, term_date
  FROM monthly_event_rollup
), all_termination_event_rollup AS (
  SELECT
    a.employeeid AS manager_id,
    a.term_date,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT a.term_type) AS distinct_term_types
  FROM hrda.all_terminations a
  INNER JOIN target_managers tm
    ON tm.manager_id = a.employeeid
  CROSS JOIN history_bounds h
  WHERE a.term_date IS NOT NULL
    AND a.term_date BETWEEN h.history_start_date AND h.history_end_date
  GROUP BY 1, 2
), all_termination_events AS (
  SELECT manager_id, term_date
  FROM all_termination_event_rollup
), event_comparison AS (
  SELECT
    COALESCE(m.manager_id, a.manager_id) AS manager_id,
    COALESCE(m.term_date, a.term_date) AS term_date,
    CASE WHEN m.manager_id IS NOT NULL THEN 1 ELSE 0 END AS in_monthly,
    CASE WHEN a.manager_id IS NOT NULL THEN 1 ELSE 0 END AS in_all_terminations
  FROM monthly_events m
  FULL OUTER JOIN all_termination_events a
    ON a.manager_id = m.manager_id
   AND a.term_date = m.term_date
), event_reconciliation AS (
  SELECT
    COUNT(*) AS comparable_event_count,
    SUM(CASE WHEN in_monthly = 1 AND in_all_terminations = 1 THEN 1 ELSE 0 END) AS matched_event_count,
    SUM(CASE WHEN in_monthly = 1 AND in_all_terminations = 0 THEN 1 ELSE 0 END) AS monthly_only_event_count,
    SUM(CASE WHEN in_monthly = 0 AND in_all_terminations = 1 THEN 1 ELSE 0 END) AS all_terminations_only_event_count
  FROM event_comparison
), event_quality AS (
  SELECT
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS monthly_repeated_event_rows,
    COALESCE(SUM(CASE WHEN distinct_term_types > 1 THEN 1 ELSE 0 END), 0) AS monthly_term_type_conflict_event_count
  FROM monthly_event_rollup
), all_event_quality AS (
  SELECT
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS all_terminations_duplicate_event_rows,
    COALESCE(SUM(CASE WHEN distinct_term_types > 1 THEN 1 ELSE 0 END), 0) AS all_terminations_term_type_conflict_event_count
  FROM all_termination_event_rollup
)
SELECT
  'Manager leaving' AS variable_name,
  q.observations_checked,
  q.months_checked,
  q.invalid_flag_rows,
  q.flagged_without_date_rows,
  q.future_positive_flag_rows,
  q.current_episode_date_without_positive_flag_rows,
  q.positive_flag_before_episode_start_rows,
  q.historical_term_carried_into_rehire_rows,
  r.relationship_rows_checked,
  r.future_manager_effective_date_rows,
  r.missing_manager_effective_date_rows,
  c.comparable_event_count,
  c.matched_event_count,
  c.monthly_only_event_count,
  c.all_terminations_only_event_count,
  e.monthly_repeated_event_rows,
  e.monthly_term_type_conflict_event_count,
  a.all_terminations_duplicate_event_rows,
  a.all_terminations_term_type_conflict_event_count,
  (
    q.invalid_flag_rows
    + q.flagged_without_date_rows
    + q.future_positive_flag_rows
    + q.current_episode_date_without_positive_flag_rows
    + q.positive_flag_before_episode_start_rows
    + r.future_manager_effective_date_rows
    + c.monthly_only_event_count
    + c.all_terminations_only_event_count
    + e.monthly_term_type_conflict_event_count
    + a.all_terminations_term_type_conflict_event_count
  ) AS anomaly_count,
  (
    q.invalid_flag_rows
    + q.flagged_without_date_rows
    + q.future_positive_flag_rows
    + q.positive_flag_before_episode_start_rows
    + r.future_manager_effective_date_rows
  ) AS invalid_count,
  (
    c.monthly_only_event_count
    + c.all_terminations_only_event_count
    + e.monthly_term_type_conflict_event_count
    + a.all_terminations_term_type_conflict_event_count
  ) AS unexplained_change_count
FROM monthly_row_quality q
CROSS JOIN relationship_row_quality r
CROSS JOIN event_reconciliation c
CROSS JOIN event_quality e
CROSS JOIN all_event_quality a;

