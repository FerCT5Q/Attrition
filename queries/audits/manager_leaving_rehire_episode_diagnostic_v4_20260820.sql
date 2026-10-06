WITH target_population AS (
  SELECT
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
), events AS (
  SELECT
    a.employeeid AS manager_id,
    a.term_date,
    a.max_hire_rehire_date,
    a.is_rehire
  FROM hrda.all_terminations a
  INNER JOIN target_managers tm
    ON tm.manager_id = a.employeeid
  CROSS JOIN history_bounds h
  WHERE a.term_date BETWEEN h.history_start_date AND h.history_end_date
), prior_episode_events AS (
  SELECT manager_id, term_date, max_hire_rehire_date, is_rehire
  FROM events
  WHERE max_hire_rehire_date IS NOT NULL
    AND term_date < max_hire_rehire_date
), monthly_history_confirmation AS (
  SELECT
    e.manager_id,
    e.term_date,
    e.max_hire_rehire_date,
    e.is_rehire,
    MAX(
      CASE
        WHEN m.employee_id IS NOT NULL
         AND m.fis_mo_end_dt >= e.max_hire_rehire_date
        THEN 1 ELSE 0
      END
    ) AS has_monthly_history_on_or_after_rehire
  FROM prior_episode_events e
  LEFT JOIN hrda.post_hire_monthly_worker_dtls m
    ON m.employee_id = e.manager_id
  GROUP BY 1, 2, 3, 4
), manager_event_counts AS (
  SELECT manager_id, COUNT(*) AS event_count
  FROM events
  GROUP BY 1
)
SELECT
  'Manager leaving' AS variable_name,
  COUNT(*) AS term_before_latest_hire_event_count,
  SUM(CASE WHEN COALESCE(is_rehire, 0) = 1 THEN 1 ELSE 0 END) AS rehire_flag_positive_count,
  SUM(CASE WHEN COALESCE(is_rehire, 0) <> 1 THEN 1 ELSE 0 END) AS rehire_flag_not_positive_count,
  SUM(CASE WHEN has_monthly_history_on_or_after_rehire = 1 THEN 1 ELSE 0 END) AS monthly_rehire_history_confirmed_count,
  SUM(CASE WHEN has_monthly_history_on_or_after_rehire = 0 THEN 1 ELSE 0 END) AS monthly_rehire_history_unconfirmed_count,
  SUM(CASE WHEN c.event_count > 1 THEN 1 ELSE 0 END) AS events_for_managers_with_multiple_terminations_count
FROM monthly_history_confirmation h
INNER JOIN manager_event_counts c
  ON c.manager_id = h.manager_id;

