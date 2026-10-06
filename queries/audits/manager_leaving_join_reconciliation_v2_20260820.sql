WITH target_raw AS (
  SELECT
    employee_id,
    fis_mo_end_dt AS snapshot_date,
    CAST(manager_employee_id AS BIGINT) AS manager_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
), history_bounds AS (
  SELECT MIN(snapshot_date) AS history_start_date, MAX(snapshot_date) AS history_end_date
  FROM target_raw
), snapshot_calendar AS (
  SELECT DISTINCT snapshot_date
  FROM target_raw
  WHERE snapshot_date IS NOT NULL
), target_snapshot_key_rollup AS (
  SELECT
    employee_id,
    snapshot_date,
    MAX(manager_id) AS manager_id,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT manager_id) AS distinct_manager_count
  FROM target_raw
  WHERE employee_id IS NOT NULL
    AND snapshot_date IS NOT NULL
  GROUP BY 1, 2
), target_snapshots AS (
  SELECT employee_id, snapshot_date, manager_id
  FROM target_snapshot_key_rollup
), target_quality AS (
  SELECT
    COUNT(*) AS eligible_count,
    SUM(CASE WHEN manager_id IS NULL THEN 1 ELSE 0 END) AS missing_manager_id_snapshot_count,
    SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END) AS raw_employee_snapshot_duplicate_rows,
    SUM(CASE WHEN distinct_manager_count > 1 THEN 1 ELSE 0 END) AS conflicting_manager_snapshot_count
  FROM target_snapshot_key_rollup
), target_manager_ids AS (
  SELECT DISTINCT manager_id
  FROM target_snapshots
  WHERE manager_id IS NOT NULL
), termination_event_rollup AS (
  SELECT
    a.employeeid AS manager_id,
    a.term_date,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT a.term_type) AS distinct_term_types
  FROM hrda.all_terminations a
  INNER JOIN target_manager_ids t
    ON t.manager_id = a.employeeid
  CROSS JOIN history_bounds h
  WHERE a.term_date IS NOT NULL
    AND a.term_date BETWEEN h.history_start_date AND h.history_end_date
  GROUP BY 1, 2
), canonical_events AS (
  SELECT manager_id, term_date
  FROM termination_event_rollup
), event_knowledge_period AS (
  SELECT
    e.manager_id,
    e.term_date,
    MIN(c.snapshot_date) AS knowledge_snapshot_date
  FROM canonical_events e
  LEFT JOIN snapshot_calendar c
    ON c.snapshot_date >= e.term_date
  GROUP BY 1, 2
), event_knowledge_quality AS (
  SELECT
    COUNT(*) AS manager_event_count,
    SUM(CASE WHEN knowledge_snapshot_date IS NOT NULL THEN 1 ELSE 0 END) AS manager_event_knowledge_matched_count,
    SUM(CASE WHEN knowledge_snapshot_date IS NULL THEN 1 ELSE 0 END) AS manager_event_knowledge_unmatched_count,
    0 AS manager_event_knowledge_multi_match_count
  FROM event_knowledge_period
), relationship_candidates AS (
  SELECT
    e.manager_id,
    e.term_date,
    e.knowledge_snapshot_date,
    s.employee_id,
    s.snapshot_date
  FROM event_knowledge_period e
  INNER JOIN target_snapshots s
    ON s.manager_id = e.manager_id
   AND s.employee_id <> e.manager_id
   AND s.snapshot_date < e.term_date
   AND s.snapshot_date >= DATEADD(day, -45, e.term_date)
  WHERE e.knowledge_snapshot_date IS NOT NULL
), latest_relationship AS (
  SELECT
    manager_id,
    term_date,
    knowledge_snapshot_date,
    employee_id,
    MAX(snapshot_date) AS prior_relationship_snapshot_date,
    COUNT(DISTINCT snapshot_date) AS candidate_snapshot_count
  FROM relationship_candidates
  GROUP BY 1, 2, 3, 4
), selected_relationship_match AS (
  SELECT
    r.manager_id,
    r.term_date,
    r.employee_id,
    COUNT(s.snapshot_date) AS match_count
  FROM latest_relationship r
  LEFT JOIN target_snapshots s
    ON s.employee_id = r.employee_id
   AND s.snapshot_date = r.prior_relationship_snapshot_date
   AND s.manager_id = r.manager_id
  GROUP BY 1, 2, 3
), attribution_quality AS (
  SELECT
    COUNT(*) AS attributed_employee_event_count,
    SUM(CASE WHEN match_count = 0 THEN 1 ELSE 0 END) AS attribution_unmatched_count,
    SUM(CASE WHEN match_count > 1 THEN 1 ELSE 0 END) AS attribution_multi_match_count
  FROM selected_relationship_match
), event_team_rollup AS (
  SELECT
    e.manager_id,
    e.term_date,
    COUNT(r.employee_id) AS attributed_employee_count
  FROM event_knowledge_period e
  LEFT JOIN latest_relationship r
    ON r.manager_id = e.manager_id
   AND r.term_date = e.term_date
  GROUP BY 1, 2
), event_team_quality AS (
  SELECT
    SUM(CASE WHEN attributed_employee_count > 0 THEN 1 ELSE 0 END) AS manager_event_with_prior_team_count,
    SUM(CASE WHEN attributed_employee_count = 0 THEN 1 ELSE 0 END) AS manager_event_without_prior_team_count
  FROM event_team_rollup
), exposure_events AS (
  SELECT
    employee_id,
    manager_id,
    term_date,
    knowledge_snapshot_date
  FROM latest_relationship
), derived_output AS (
  SELECT
    s.employee_id,
    s.snapshot_date,
    COUNT(e.term_date) AS manager_leaving_events_known_by_snapshot
  FROM target_snapshots s
  LEFT JOIN exposure_events e
    ON e.employee_id = s.employee_id
   AND e.knowledge_snapshot_date <= s.snapshot_date
   AND e.term_date <= s.snapshot_date
  GROUP BY 1, 2
), derived_key_rollup AS (
  SELECT employee_id, snapshot_date, COUNT(*) AS derived_rows
  FROM derived_output
  GROUP BY 1, 2
), output_match AS (
  SELECT
    s.employee_id,
    s.snapshot_date,
    COUNT(d.snapshot_date) AS match_count
  FROM target_snapshots s
  LEFT JOIN derived_key_rollup d
    ON d.employee_id = s.employee_id
   AND d.snapshot_date = s.snapshot_date
  GROUP BY 1, 2
), output_quality AS (
  SELECT
    SUM(CASE WHEN match_count = 1 THEN 1 ELSE 0 END) AS matched_count,
    SUM(CASE WHEN match_count = 0 THEN 1 ELSE 0 END) AS unmatched_count,
    SUM(CASE WHEN match_count > 1 THEN match_count - 1 ELSE 0 END) AS duplicate_count,
    SUM(CASE WHEN match_count > 1 THEN 1 ELSE 0 END) AS multi_match_count
  FROM output_match
), event_quality AS (
  SELECT
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS duplicate_manager_event_rows,
    COALESCE(SUM(CASE WHEN distinct_term_types > 1 THEN 1 ELSE 0 END), 0) AS manager_event_term_type_conflicts
  FROM termination_event_rollup
), exposure_quality AS (
  SELECT
    SUM(CASE WHEN term_date > knowledge_snapshot_date THEN 1 ELSE 0 END) AS future_event_usage_count,
    SUM(CASE WHEN candidate_snapshot_count > 1 THEN 1 ELSE 0 END) AS employee_events_with_multiple_prior_candidates,
    MAX(DATEDIFF(day, prior_relationship_snapshot_date, term_date)) AS maximum_prior_relationship_lag_days
  FROM latest_relationship
), manager_snapshot_keys AS (
  SELECT DISTINCT employee_id AS manager_id, fis_mo_end_dt AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE employee_id IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
), same_snapshot_unmatched AS (
  SELECT s.employee_id, s.snapshot_date, s.manager_id
  FROM target_snapshots s
  LEFT JOIN manager_snapshot_keys m
    ON m.manager_id = s.manager_id
   AND m.snapshot_date = s.snapshot_date
  WHERE s.manager_id IS NOT NULL
    AND m.manager_id IS NULL
), unmatched_resolution AS (
  SELECT
    u.employee_id,
    u.snapshot_date,
    u.manager_id,
    MAX(CASE WHEN m.manager_id IS NOT NULL THEN 1 ELSE 0 END) AS found_any_history,
    MAX(
      CASE
        WHEN m.manager_id IS NOT NULL
         AND ABS(DATEDIFF(day, m.snapshot_date, u.snapshot_date)) <= 45
        THEN 1 ELSE 0
      END
    ) AS found_within_45_days
  FROM same_snapshot_unmatched u
  LEFT JOIN manager_snapshot_keys m
    ON m.manager_id = u.manager_id
  GROUP BY 1, 2, 3
), unmatched_diagnostics AS (
  SELECT
    COUNT(*) AS same_snapshot_manager_unmatched_count,
    SUM(CASE WHEN found_any_history = 1 THEN 1 ELSE 0 END) AS unmatched_manager_found_any_history_count,
    SUM(CASE WHEN found_within_45_days = 1 THEN 1 ELSE 0 END) AS unmatched_manager_found_within_45_days_count,
    SUM(CASE WHEN found_any_history = 0 THEN 1 ELSE 0 END) AS unmatched_manager_never_found_count
  FROM unmatched_resolution
)
SELECT
  'Manager leaving' AS variable_name,
  t.eligible_count,
  o.matched_count,
  o.unmatched_count,
  o.duplicate_count,
  o.multi_match_count,
  t.missing_manager_id_snapshot_count,
  t.raw_employee_snapshot_duplicate_rows,
  t.conflicting_manager_snapshot_count,
  k.manager_event_count,
  k.manager_event_knowledge_matched_count,
  k.manager_event_knowledge_unmatched_count,
  k.manager_event_knowledge_multi_match_count,
  a.attributed_employee_event_count,
  a.attribution_unmatched_count,
  a.attribution_multi_match_count,
  e.manager_event_with_prior_team_count,
  e.manager_event_without_prior_team_count,
  q.duplicate_manager_event_rows,
  q.manager_event_term_type_conflicts,
  x.future_event_usage_count,
  x.employee_events_with_multiple_prior_candidates,
  x.maximum_prior_relationship_lag_days,
  d.same_snapshot_manager_unmatched_count,
  d.unmatched_manager_found_any_history_count,
  d.unmatched_manager_found_within_45_days_count,
  d.unmatched_manager_never_found_count
FROM target_quality t
CROSS JOIN output_quality o
CROSS JOIN event_knowledge_quality k
CROSS JOIN attribution_quality a
CROSS JOIN event_team_quality e
CROSS JOIN event_quality q
CROSS JOIN exposure_quality x
CROSS JOIN unmatched_diagnostics d;

