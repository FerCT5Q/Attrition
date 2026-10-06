WITH target_raw AS (
  SELECT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
), target_rollup AS (
  SELECT
    employee_id,
    snapshot_date,
    MAX(manager_employee_id) AS manager_employee_id,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT manager_employee_id) AS manager_values
  FROM target_raw
  GROUP BY employee_id, snapshot_date
), target AS (
  SELECT employee_id, snapshot_date, manager_employee_id
  FROM target_rollup
  WHERE raw_rows = 1
    AND manager_values <= 1
), bounds AS (
  SELECT MIN(snapshot_date) AS min_snapshot_date, MAX(snapshot_date) AS max_snapshot_date
  FROM target
), calendar AS (
  SELECT DISTINCT snapshot_date
  FROM target
), target_people AS (
  SELECT DISTINCT employee_id
  FROM target
), event_source AS (
  SELECT
    a.employeeid,
    a.term_date,
    LOWER(TRIM(a.term_type)) AS normalized_term_type
  FROM hrda.all_terminations a
  INNER JOIN target_people p
    ON p.employee_id = a.employeeid
  CROSS JOIN bounds b
  WHERE a.term_date BETWEEN b.min_snapshot_date AND b.max_snapshot_date
    AND LOWER(TRIM(a.term_type)) IN ('voluntary', 'voluntary exception')
), events AS (
  SELECT
    employeeid,
    term_date,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT normalized_term_type) AS term_type_values
  FROM event_source
  GROUP BY employeeid, term_date
), prior_candidates AS (
  SELECT
    e.employeeid,
    e.term_date,
    t.snapshot_date,
    t.manager_employee_id,
    MAX(t.snapshot_date) OVER (PARTITION BY e.employeeid, e.term_date) AS latest_prior_snapshot
  FROM events e
  INNER JOIN target t
    ON t.employee_id = e.employeeid
   AND t.manager_employee_id IS NOT NULL
   AND t.snapshot_date < e.term_date
   AND DATEDIFF(day, t.snapshot_date, e.term_date) BETWEEN 0 AND 45
), prior_summary AS (
  SELECT
    e.employeeid,
    e.term_date,
    e.raw_rows,
    e.term_type_values,
    COUNT(p.snapshot_date) AS candidate_count,
    COALESCE(SUM(CASE WHEN p.snapshot_date = p.latest_prior_snapshot THEN 1 ELSE 0 END), 0) AS latest_candidate_count,
    MAX(CASE WHEN p.snapshot_date = p.latest_prior_snapshot THEN p.snapshot_date END) AS attributed_snapshot_date,
    MAX(CASE WHEN p.snapshot_date = p.latest_prior_snapshot THEN p.manager_employee_id END) AS attributed_manager_id
  FROM events e
  LEFT JOIN prior_candidates p
    ON p.employeeid = e.employeeid
   AND p.term_date = e.term_date
  GROUP BY e.employeeid, e.term_date, e.raw_rows, e.term_type_values
), knowledge_candidates AS (
  SELECT
    p.employeeid,
    p.term_date,
    c.snapshot_date,
    MIN(c.snapshot_date) OVER (PARTITION BY p.employeeid, p.term_date) AS first_known_snapshot
  FROM prior_summary p
  INNER JOIN calendar c
    ON c.snapshot_date >= p.term_date
  WHERE p.candidate_count > 0
), knowledge_summary AS (
  SELECT
    p.employeeid,
    p.term_date,
    COUNT(CASE WHEN k.snapshot_date = k.first_known_snapshot THEN 1 END) AS first_known_candidate_count,
    MAX(CASE WHEN k.snapshot_date = k.first_known_snapshot THEN k.snapshot_date END) AS first_known_snapshot
  FROM prior_summary p
  LEFT JOIN knowledge_candidates k
    ON k.employeeid = p.employeeid
   AND k.term_date = p.term_date
  WHERE p.candidate_count > 0
  GROUP BY p.employeeid, p.term_date
), manager_snapshots AS (
  SELECT DISTINCT manager_employee_id AS manager_id, snapshot_date
  FROM target
  WHERE manager_employee_id IS NOT NULL
), feature_assignment AS (
  SELECT
    t.employee_id,
    t.snapshot_date,
    COUNT(m.manager_id) AS match_count
  FROM target t
  LEFT JOIN manager_snapshots m
    ON m.manager_id = t.manager_employee_id
   AND m.snapshot_date = t.snapshot_date
  WHERE t.manager_employee_id IS NOT NULL
  GROUP BY t.employee_id, t.snapshot_date
), event_metrics AS (
  SELECT
    COALESCE(SUM(CASE WHEN candidate_count > 0 THEN 1 ELSE 0 END), 0) AS eligible_count,
    COALESCE(SUM(CASE WHEN candidate_count > 0 AND latest_candidate_count = 1 THEN 1 ELSE 0 END), 0) AS matched_count,
    COALESCE(SUM(CASE WHEN candidate_count > 0 AND latest_candidate_count = 0 THEN 1 ELSE 0 END), 0) AS unmatched_count,
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS duplicate_count,
    COALESCE(SUM(CASE WHEN latest_candidate_count > 1 OR term_type_values > 1 THEN 1 ELSE 0 END), 0) AS multi_match_count,
    COALESCE(SUM(CASE WHEN candidate_count = 0 THEN 1 ELSE 0 END), 0) AS excluded_without_target_snapshot_count,
    COUNT(*) AS voluntary_event_count
  FROM prior_summary
), knowledge_metrics AS (
  SELECT
    COALESCE(SUM(CASE WHEN first_known_candidate_count = 0 THEN 1 ELSE 0 END), 0) AS knowledge_unmatched_count,
    COALESCE(SUM(CASE WHEN first_known_candidate_count > 1 THEN 1 ELSE 0 END), 0) AS knowledge_multi_match_count,
    COALESCE(SUM(CASE WHEN first_known_snapshot < term_date THEN 1 ELSE 0 END), 0) AS future_event_usage_count
  FROM knowledge_summary
), assignment_metrics AS (
  SELECT
    COUNT(*) AS feature_assignment_eligible_count,
    COALESCE(SUM(CASE WHEN match_count = 1 THEN 1 ELSE 0 END), 0) AS feature_assignment_matched_count,
    COALESCE(SUM(CASE WHEN match_count = 0 THEN 1 ELSE 0 END), 0) AS feature_assignment_unmatched_count,
    COALESCE(SUM(CASE WHEN match_count > 1 THEN 1 ELSE 0 END), 0) AS feature_assignment_multi_match_count
  FROM feature_assignment
), raw_quality AS (
  SELECT
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS raw_employee_snapshot_duplicate_rows,
    COALESCE(SUM(CASE WHEN manager_values > 1 THEN 1 ELSE 0 END), 0) AS conflicting_manager_snapshot_count
  FROM target_rollup
)
SELECT
  'High risk manager' AS variable_name,
  e.eligible_count,
  e.matched_count,
  e.unmatched_count,
  e.duplicate_count,
  e.multi_match_count,
  e.voluntary_event_count,
  e.excluded_without_target_snapshot_count,
  k.knowledge_unmatched_count,
  k.knowledge_multi_match_count,
  a.feature_assignment_eligible_count,
  a.feature_assignment_matched_count,
  a.feature_assignment_unmatched_count,
  a.feature_assignment_multi_match_count,
  q.raw_employee_snapshot_duplicate_rows,
  q.conflicting_manager_snapshot_count,
  k.future_event_usage_count
FROM event_metrics e
CROSS JOIN knowledge_metrics k
CROSS JOIN assignment_metrics a
CROSS JOIN raw_quality q;
