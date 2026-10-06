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
), source_rows AS (
  SELECT
    a.employeeid AS manager_id,
    a.term_date,
    a.term_type,
    a.max_hire_rehire_date
  FROM hrda.all_terminations a
  INNER JOIN target_managers tm
    ON tm.manager_id = a.employeeid
), relevant_rows AS (
  SELECT
    s.manager_id,
    s.term_date,
    s.term_type,
    s.max_hire_rehire_date
  FROM source_rows s
  CROSS JOIN history_bounds h
  WHERE s.term_date BETWEEN h.history_start_date AND h.history_end_date
), row_quality AS (
  SELECT
    COUNT(*) AS observations_checked,
    COUNT(DISTINCT DATE_TRUNC('month', term_date)) AS months_checked,
    SUM(CASE WHEN term_date IS NULL THEN 1 ELSE 0 END) AS null_term_date_rows,
    SUM(CASE WHEN term_type IS NULL OR NULLIF(TRIM(term_type), '') IS NULL THEN 1 ELSE 0 END) AS null_or_blank_term_type_rows,
    SUM(
      CASE
        WHEN max_hire_rehire_date IS NOT NULL
         AND term_date < max_hire_rehire_date
        THEN 1 ELSE 0
      END
    ) AS term_before_episode_start_rows
  FROM relevant_rows
), source_boundary_quality AS (
  SELECT
    SUM(CASE WHEN term_date > h.history_end_date THEN 1 ELSE 0 END) AS source_events_after_history_count,
    SUM(CASE WHEN term_date < h.history_start_date THEN 1 ELSE 0 END) AS source_events_before_history_count
  FROM source_rows
  CROSS JOIN history_bounds h
), event_rollup AS (
  SELECT
    manager_id,
    term_date,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT term_type) AS distinct_term_types,
    COUNT(DISTINCT max_hire_rehire_date) AS distinct_episode_starts
  FROM relevant_rows
  GROUP BY 1, 2
), event_quality AS (
  SELECT
    COUNT(*) AS event_key_count,
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS duplicate_event_rows,
    COALESCE(SUM(CASE WHEN distinct_term_types > 1 THEN 1 ELSE 0 END), 0) AS term_type_conflict_event_count,
    COALESCE(SUM(CASE WHEN distinct_episode_starts > 1 THEN 1 ELSE 0 END), 0) AS episode_start_conflict_event_count
  FROM event_rollup
), type_domain AS (
  SELECT
    COUNT(DISTINCT term_type) AS raw_term_type_count,
    COUNT(DISTINCT LOWER(TRIM(term_type))) AS normalized_term_type_count
  FROM relevant_rows
  WHERE term_type IS NOT NULL
    AND NULLIF(TRIM(term_type), '') IS NOT NULL
)
SELECT
  'Manager leaving' AS variable_name,
  r.observations_checked,
  r.months_checked,
  e.event_key_count,
  r.null_term_date_rows,
  r.null_or_blank_term_type_rows,
  r.term_before_episode_start_rows,
  e.duplicate_event_rows,
  e.term_type_conflict_event_count,
  e.episode_start_conflict_event_count,
  d.raw_term_type_count,
  d.normalized_term_type_count,
  (d.raw_term_type_count - d.normalized_term_type_count) AS term_type_normalization_collision_count,
  b.source_events_after_history_count,
  b.source_events_before_history_count,
  (
    r.null_term_date_rows
    + r.term_before_episode_start_rows
    + e.duplicate_event_rows
    + e.term_type_conflict_event_count
    + e.episode_start_conflict_event_count
    + (d.raw_term_type_count - d.normalized_term_type_count)
  ) AS anomaly_count,
  (
    r.null_term_date_rows
    + r.term_before_episode_start_rows
  ) AS invalid_count,
  (
    e.duplicate_event_rows
    + e.term_type_conflict_event_count
    + e.episode_start_conflict_event_count
    + (d.raw_term_type_count - d.normalized_term_type_count)
  ) AS unexplained_change_count
FROM row_quality r
CROSS JOIN source_boundary_quality b
CROSS JOIN event_quality e
CROSS JOIN type_domain d;
