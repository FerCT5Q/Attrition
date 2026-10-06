WITH population_rows AS (
  SELECT
    employee_id,
    fis_mo_beg_dt,
    fis_mo_end_dt,
    manager_change,
    manager_change_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
), history_bounds AS (
  SELECT
    MIN(fis_mo_beg_dt) AS history_start_date,
    MAX(fis_mo_end_dt) AS history_end_date
  FROM population_rows
), snapshot_key_rollup AS (
  SELECT
    employee_id,
    fis_mo_end_dt AS snapshot_date,
    MIN(fis_mo_beg_dt) AS snapshot_begin_date,
    MAX(fis_mo_end_dt) AS snapshot_end_date,
    COUNT(*) AS raw_rows
  FROM population_rows
  WHERE employee_id IS NOT NULL
    AND fis_mo_beg_dt IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY 1, 2
), snapshots AS (
  SELECT
    employee_id,
    snapshot_date,
    snapshot_begin_date,
    snapshot_end_date
  FROM snapshot_key_rollup
), snapshot_quality AS (
  SELECT
    COUNT(*) AS eligible_count,
    SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END) AS duplicate_count,
    SUM(CASE WHEN raw_rows > 1 THEN 1 ELSE 0 END) AS duplicate_snapshot_key_count
  FROM snapshot_key_rollup
), event_row_quality AS (
  SELECT
    SUM(CASE WHEN COALESCE(manager_change, 0) > 0 AND manager_change_date IS NULL THEN 1 ELSE 0 END) AS flagged_without_date_rows,
    SUM(CASE WHEN COALESCE(manager_change, 0) > 0 AND manager_change_date > fis_mo_end_dt THEN 1 ELSE 0 END) AS future_positive_flag_rows,
    SUM(CASE WHEN manager_change IS NOT NULL AND manager_change NOT IN (0, 1) THEN 1 ELSE 0 END) AS invalid_flag_rows
  FROM population_rows
), event_key_rollup AS (
  SELECT
    employee_id,
    manager_change_date AS event_date,
    MAX(CASE WHEN COALESCE(manager_change, 0) > 0 THEN 1 ELSE 0 END) AS has_positive_flag,
    COUNT(*) AS observation_rows,
    SUM(CASE WHEN COALESCE(manager_change, 0) > 0 THEN 1 ELSE 0 END) AS positive_flag_rows
  FROM population_rows
  WHERE employee_id IS NOT NULL
    AND manager_change_date IS NOT NULL
  GROUP BY 1, 2
), canonical_events AS (
  SELECT
    e.employee_id,
    e.event_date
  FROM event_key_rollup e
  CROSS JOIN history_bounds h
  WHERE e.has_positive_flag = 1
    AND e.event_date BETWEEN h.history_start_date AND h.history_end_date
), event_diagnostics AS (
  SELECT
    SUM(CASE WHEN has_positive_flag = 0 THEN 1 ELSE 0 END) AS date_without_positive_flag_key_count,
    SUM(CASE WHEN has_positive_flag = 1 AND observation_rows > 1 THEN observation_rows - 1 ELSE 0 END) AS repeated_event_observation_rows,
    SUM(CASE WHEN has_positive_flag = 1 AND event_date < h.history_start_date THEN 1 ELSE 0 END) AS prehistory_event_count
  FROM event_key_rollup
  CROSS JOIN history_bounds h
), event_snapshot_match AS (
  SELECT
    e.employee_id,
    e.event_date,
    COUNT(s.snapshot_date) AS match_count
  FROM canonical_events e
  LEFT JOIN snapshots s
    ON s.employee_id = e.employee_id
   AND e.event_date BETWEEN s.snapshot_begin_date AND s.snapshot_end_date
  GROUP BY 1, 2
), event_join_quality AS (
  SELECT
    COUNT(*) AS eligible_event_count,
    SUM(CASE WHEN match_count = 1 THEN 1 ELSE 0 END) AS matched_event_count,
    SUM(CASE WHEN match_count = 0 THEN 1 ELSE 0 END) AS unmatched_event_count,
    SUM(CASE WHEN match_count > 1 THEN 1 ELSE 0 END) AS multi_match_event_count,
    100.0 * SUM(CASE WHEN match_count = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS event_match_rate_percent
  FROM event_snapshot_match
), derived_output AS (
  SELECT
    s.employee_id,
    s.snapshot_date,
    COUNT(e.event_date) AS manager_change_count_through_snapshot
  FROM snapshots s
  LEFT JOIN canonical_events e
    ON e.employee_id = s.employee_id
   AND e.event_date <= s.snapshot_date
  GROUP BY 1, 2
), derived_key_rollup AS (
  SELECT
    employee_id,
    snapshot_date,
    COUNT(*) AS derived_rows
  FROM derived_output
  GROUP BY 1, 2
), snapshot_output_match AS (
  SELECT
    s.employee_id,
    s.snapshot_date,
    COUNT(d.snapshot_date) AS match_count
  FROM snapshots s
  LEFT JOIN derived_key_rollup d
    ON d.employee_id = s.employee_id
   AND d.snapshot_date = s.snapshot_date
  GROUP BY 1, 2
), output_join_quality AS (
  SELECT
    COUNT(*) AS output_eligible_count,
    SUM(CASE WHEN match_count = 1 THEN 1 ELSE 0 END) AS matched_count,
    SUM(CASE WHEN match_count = 0 THEN 1 ELSE 0 END) AS unmatched_count,
    SUM(CASE WHEN match_count > 1 THEN 1 ELSE 0 END) AS multi_match_count,
    100.0 * SUM(CASE WHEN match_count = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS match_rate_percent
  FROM snapshot_output_match
)
SELECT
  'Number of manager changes' AS variable_name,
  s.eligible_count,
  o.matched_count,
  o.unmatched_count,
  s.duplicate_count,
  o.multi_match_count,
  o.match_rate_percent,
  s.duplicate_snapshot_key_count,
  e.eligible_event_count,
  e.matched_event_count,
  e.unmatched_event_count,
  e.multi_match_event_count,
  e.event_match_rate_percent,
  q.flagged_without_date_rows,
  q.future_positive_flag_rows,
  q.invalid_flag_rows,
  d.date_without_positive_flag_key_count,
  d.repeated_event_observation_rows,
  d.prehistory_event_count
FROM snapshot_quality s
CROSS JOIN output_join_quality o
CROSS JOIN event_join_quality e
CROSS JOIN event_row_quality q
CROSS JOIN event_diagnostics d;
