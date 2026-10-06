-- Claim: More than 1 employee leaves is a time-safe monthly employee exposure
-- series reconstructed at the employee-month snapshot grain.
-- Deliverable mode: presentation; aggregate-only output.
--
-- At evaluation snapshot t:
--   Eligible team = employees with a non-null direct manager at t. The
--                  teams_gt_5 scope keeps only managers with >= 6 reports.
--   Eligible exit = one distinct employee/term_date event with term_type
--                  exactly Voluntary and term_date in (t - 6 months, t].
--   Flagged employee = an observable employee whose team has >= 2 eligible
--                      exits in the same six-month window.
--
-- The result contains two independent attribution series per scope and
-- snapshot. The 0/1/2+ team-snapshot buckets remain as audit evidence, but
-- the monthly employee series is the publication metric.

WITH RECURSIVE
parameters AS (
  SELECT DATE '2026-08-23' AS cutoff_date
),
raw_monthly_rows AS (
  SELECT
    CAST(worker.fis_mo_end_dt AS DATE) AS snapshot_date,
    worker.employee_id,
    worker.manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls AS worker
  CROSS JOIN parameters
  WHERE CAST(worker.fis_mo_end_dt AS DATE) <= parameters.cutoff_date
    AND worker.worker_type = 'Employee'
    AND worker.employee_type = 'Regular'
    AND worker.active_status = 1
),
raw_monthly AS (
  SELECT DISTINCT snapshot_date, employee_id, manager_employee_id
  FROM raw_monthly_rows
),
snapshot_dates AS (
  SELECT snapshot_date FROM raw_monthly GROUP BY 1
),
valid_evaluation_snapshots AS (
  SELECT s.snapshot_date, COUNT(DISTINCT w.snapshot_date) AS window_snapshot_count
  FROM snapshot_dates AS s
  LEFT JOIN snapshot_dates AS w
    ON w.snapshot_date > DATEADD(month, -6, s.snapshot_date)
   AND w.snapshot_date <= s.snapshot_date
  GROUP BY 1
  HAVING COUNT(DISTINCT w.snapshot_date) = 6
),
membership AS (
  SELECT r.snapshot_date, r.employee_id, r.manager_employee_id
  FROM raw_monthly AS r
  INNER JOIN valid_evaluation_snapshots AS v ON v.snapshot_date = r.snapshot_date
  WHERE r.manager_employee_id IS NOT NULL
),
team_sizes AS (
  SELECT snapshot_date, manager_employee_id, COUNT(DISTINCT employee_id) AS direct_reports
  FROM membership
  GROUP BY 1, 2
),
scopes AS (
  SELECT 'all_teams' AS scope, 1 AS minimum_direct_reports
  UNION ALL SELECT 'teams_gt_5' AS scope, 6 AS minimum_direct_reports
),
team_snapshot_groups AS (
  SELECT s.scope, t.snapshot_date, t.manager_employee_id, t.direct_reports
  FROM team_sizes AS t
  CROSS JOIN scopes AS s
  WHERE t.direct_reports >= s.minimum_direct_reports
),
scope_employee_rows AS (
  SELECT DISTINCT g.scope, g.snapshot_date, m.employee_id, m.manager_employee_id
  FROM team_snapshot_groups AS g
  INNER JOIN membership AS m
    ON m.snapshot_date = g.snapshot_date
   AND m.manager_employee_id = g.manager_employee_id
),
voluntary_events AS (
  SELECT worker.employee_id, CAST(worker.term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls AS worker
  CROSS JOIN parameters
  WHERE CAST(worker.term_date AS DATE) <= parameters.cutoff_date
    AND CAST(worker.term_date AS DATE) > DATEADD(
      month, -6, (SELECT MIN(snapshot_date) FROM valid_evaluation_snapshots)
    )
    AND UPPER(NULLIF(TRIM(CAST(worker.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
),
manager_at_exit_candidates AS (
  SELECT e.employee_id, e.term_date, h.manager_employee_id,
    ROW_NUMBER() OVER (
      PARTITION BY e.employee_id, e.term_date
      ORDER BY h.snapshot_date DESC, h.manager_employee_id
    ) AS manager_rank
  FROM voluntary_events AS e
  LEFT JOIN raw_monthly AS h
    ON h.employee_id = e.employee_id
   AND h.manager_employee_id IS NOT NULL
   AND h.snapshot_date <= e.term_date
),
manager_at_exit AS (
  SELECT employee_id, term_date, manager_employee_id
  FROM manager_at_exit_candidates
  WHERE manager_rank = 1 AND manager_employee_id IS NOT NULL
),
manager_at_evaluation_candidates AS (
  SELECT e.employee_id, e.term_date, v.snapshot_date, h.manager_employee_id,
    ROW_NUMBER() OVER (
      PARTITION BY e.employee_id, e.term_date, v.snapshot_date
      ORDER BY h.snapshot_date DESC, h.manager_employee_id
    ) AS manager_rank
  FROM voluntary_events AS e
  INNER JOIN valid_evaluation_snapshots AS v
    ON e.term_date <= v.snapshot_date
   AND e.term_date > DATEADD(month, -6, v.snapshot_date)
  LEFT JOIN raw_monthly AS h
    ON h.employee_id = e.employee_id
   AND h.manager_employee_id IS NOT NULL
   AND h.snapshot_date <= v.snapshot_date
),
manager_at_evaluation AS (
  SELECT employee_id, term_date, snapshot_date, manager_employee_id
  FROM manager_at_evaluation_candidates
  WHERE manager_rank = 1 AND manager_employee_id IS NOT NULL
),
manager_exit_counts AS (
  SELECT g.scope, g.snapshot_date, g.manager_employee_id,
    COUNT(DISTINCT CASE
      WHEN e.term_date > DATEADD(month, -6, g.snapshot_date)
       AND e.term_date <= g.snapshot_date
      THEN e.employee_id || '|' || e.term_date::VARCHAR END) AS exit_count
  FROM team_snapshot_groups AS g
  LEFT JOIN manager_at_exit AS e ON e.manager_employee_id = g.manager_employee_id
  GROUP BY 1, 2, 3
),
manager_evaluation_counts AS (
  SELECT g.scope, g.snapshot_date, g.manager_employee_id,
    COUNT(DISTINCT CASE
      WHEN e.snapshot_date = g.snapshot_date
      THEN e.employee_id || '|' || e.term_date::VARCHAR END) AS exit_count
  FROM team_snapshot_groups AS g
  LEFT JOIN manager_at_evaluation AS e
    ON e.snapshot_date = g.snapshot_date
   AND e.manager_employee_id = g.manager_employee_id
  GROUP BY 1, 2, 3
),
team_bucket_rows AS (
  SELECT g.scope, g.snapshot_date, g.manager_employee_id, g.direct_reports,
    CASE WHEN x.exit_count >= 2 THEN '2+' ELSE x.exit_count::VARCHAR END AS bucket,
    'manager_at_exit' AS attribution, x.exit_count
  FROM team_snapshot_groups AS g
  INNER JOIN manager_exit_counts AS x
    ON x.scope = g.scope AND x.snapshot_date = g.snapshot_date
   AND x.manager_employee_id = g.manager_employee_id
  UNION ALL
  SELECT g.scope, g.snapshot_date, g.manager_employee_id, g.direct_reports,
    CASE WHEN x.exit_count >= 2 THEN '2+' ELSE x.exit_count::VARCHAR END AS bucket,
    'manager_at_evaluation' AS attribution, x.exit_count
  FROM team_snapshot_groups AS g
  INNER JOIN manager_evaluation_counts AS x
    ON x.scope = g.scope AND x.snapshot_date = g.snapshot_date
   AND x.manager_employee_id = g.manager_employee_id
),
bucket_rows AS (
  SELECT scope, attribution, bucket, COUNT(*) AS team_snapshot_groups,
    SUM(direct_reports) AS employee_snapshots, COUNT(DISTINCT snapshot_date) AS snapshots_checked
  FROM team_bucket_rows GROUP BY 1, 2, 3
),
scope_denominators AS (
  SELECT scope, COUNT(*) AS total_team_snapshot_groups,
    SUM(direct_reports) AS total_employee_snapshots, COUNT(DISTINCT snapshot_date) AS snapshots_checked
  FROM team_snapshot_groups GROUP BY 1
),
monthly_series AS (
  SELECT e.scope, 'manager_at_exit' AS attribution, e.snapshot_date,
    COUNT(DISTINCT CASE WHEN x.exit_count >= 2 THEN e.employee_id END) AS flagged_employees,
    COUNT(DISTINCT e.employee_id) AS observable_employees,
    COUNT(DISTINCT CASE WHEN x.exit_count >= 2 THEN e.manager_employee_id END) AS affected_teams
  FROM scope_employee_rows AS e
  INNER JOIN manager_exit_counts AS x
    ON x.scope = e.scope AND x.snapshot_date = e.snapshot_date
   AND x.manager_employee_id = e.manager_employee_id
  GROUP BY 1, 2, 3
  UNION ALL
  SELECT e.scope, 'manager_at_evaluation' AS attribution, e.snapshot_date,
    COUNT(DISTINCT CASE WHEN x.exit_count >= 2 THEN e.employee_id END) AS flagged_employees,
    COUNT(DISTINCT e.employee_id) AS observable_employees,
    COUNT(DISTINCT CASE WHEN x.exit_count >= 2 THEN e.manager_employee_id END) AS affected_teams
  FROM scope_employee_rows AS e
  INNER JOIN manager_evaluation_counts AS x
    ON x.scope = e.scope AND x.snapshot_date = e.snapshot_date
   AND x.manager_employee_id = e.manager_employee_id
  GROUP BY 1, 2, 3
),
monthly_output AS (
  SELECT 'monthly_series' AS row_type, s.scope, s.attribution, s.snapshot_date,
    CAST(NULL AS VARCHAR(8)) AS bucket, CAST(NULL AS BIGINT) AS team_snapshot_groups,
    CAST(NULL AS BIGINT) AS employee_snapshots, CAST(NULL AS BIGINT) AS total_team_snapshot_groups,
    CAST(NULL AS BIGINT) AS total_employee_snapshots, 1 AS snapshots_checked,
    CAST(NULL AS DECIMAL(18,4)) AS group_share_percent,
    CAST(NULL AS DECIMAL(18,4)) AS employee_snapshot_share_percent,
    s.flagged_employees, s.observable_employees,
    ROUND(100.0 * s.flagged_employees / NULLIF(s.observable_employees, 0), 6) AS employee_percent,
    s.affected_teams, CAST(NULL AS VARCHAR(128)) AS metric, CAST(NULL AS DECIMAL(18,4)) AS metric_value
  FROM monthly_series AS s
),
bucket_output AS (
  SELECT 'bucket' AS row_type, b.scope, b.attribution, CAST(NULL AS DATE) AS snapshot_date,
    b.bucket, b.team_snapshot_groups, b.employee_snapshots, d.total_team_snapshot_groups,
    d.total_employee_snapshots, b.snapshots_checked,
    ROUND(100.0 * b.team_snapshot_groups / NULLIF(d.total_team_snapshot_groups, 0), 4) AS group_share_percent,
    ROUND(100.0 * b.employee_snapshots / NULLIF(d.total_employee_snapshots, 0), 4) AS employee_snapshot_share_percent,
    CAST(NULL AS BIGINT) AS flagged_employees, CAST(NULL AS BIGINT) AS observable_employees,
    CAST(NULL AS DECIMAL(18,6)) AS employee_percent, CAST(NULL AS BIGINT) AS affected_teams,
    CAST(NULL AS VARCHAR(128)) AS metric, CAST(NULL AS DECIMAL(18,4)) AS metric_value
  FROM bucket_rows AS b INNER JOIN scope_denominators AS d ON d.scope = b.scope
),
scenario_changes AS (
  SELECT scope,
    SUM(CASE WHEN exit_bucket <> evaluation_bucket THEN 1 ELSE 0 END) AS groups_changed,
    SUM(CASE WHEN (exit_count >= 2) <> (evaluation_count >= 2) THEN 1 ELSE 0 END) AS flags_changed,
    SUM(CASE WHEN exit_count >= 2 THEN direct_reports ELSE 0 END) AS employee_snapshots_flagged_exit,
    SUM(CASE WHEN evaluation_count >= 2 THEN direct_reports ELSE 0 END) AS employee_snapshots_flagged_evaluation
  FROM (
    SELECT e.scope, e.snapshot_date, e.manager_employee_id, g.direct_reports,
      CASE WHEN e.exit_count >= 2 THEN '2+' ELSE e.exit_count::VARCHAR END AS exit_bucket,
      CASE WHEN v.exit_count >= 2 THEN '2+' ELSE v.exit_count::VARCHAR END AS evaluation_bucket,
      e.exit_count, v.exit_count AS evaluation_count
    FROM manager_exit_counts AS e
    INNER JOIN manager_evaluation_counts AS v
      ON v.scope = e.scope AND v.snapshot_date = e.snapshot_date
     AND v.manager_employee_id = e.manager_employee_id
    INNER JOIN team_snapshot_groups AS g
      ON g.scope = e.scope AND g.snapshot_date = e.snapshot_date
     AND g.manager_employee_id = e.manager_employee_id
  ) AS compared
  GROUP BY 1
),
audit_rows AS (
  SELECT 'audit' AS row_type, 'window_snapshot_count_min' AS metric, MIN(window_snapshot_count)::DECIMAL(18,4) AS metric_value FROM valid_evaluation_snapshots
  UNION ALL SELECT 'audit', 'window_snapshot_count_max', MAX(window_snapshot_count)::DECIMAL(18,4) FROM valid_evaluation_snapshots
  UNION ALL SELECT 'audit', 'evaluation_snapshots', COUNT(*)::DECIMAL(18,4) FROM valid_evaluation_snapshots
  UNION ALL SELECT 'audit', 'monthly_series_points', COUNT(*)::DECIMAL(18,4) FROM monthly_series
  UNION ALL SELECT 'audit', 'monthly_series_numerator_over_denominator', SUM(CASE WHEN flagged_employees > observable_employees THEN 1 ELSE 0 END)::DECIMAL(18,4) FROM monthly_series
  UNION ALL SELECT 'audit', 'membership_duplicate_rows', SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END)::DECIMAL(18,4) FROM (SELECT snapshot_date, employee_id, COUNT(*) AS row_count FROM raw_monthly_rows GROUP BY 1, 2) AS duplicates
  UNION ALL SELECT 'audit', 'voluntary_events', COUNT(*)::DECIMAL(18,4) FROM voluntary_events
  UNION ALL SELECT 'audit', 'voluntary_events_with_manager_at_exit', COUNT(*)::DECIMAL(18,4) FROM (SELECT DISTINCT employee_id, term_date FROM manager_at_exit) AS attributed
  UNION ALL SELECT 'audit', 'voluntary_events_unmatched_at_exit', COUNT(*)::DECIMAL(18,4) FROM voluntary_events AS e LEFT JOIN manager_at_exit AS m ON m.employee_id = e.employee_id AND m.term_date = e.term_date WHERE m.employee_id IS NULL
  UNION ALL SELECT 'audit', 'all_team_denominator_groups', total_team_snapshot_groups::DECIMAL(18,4) FROM scope_denominators WHERE scope = 'all_teams'
  UNION ALL SELECT 'audit', 'large_team_denominator_groups', total_team_snapshot_groups::DECIMAL(18,4) FROM scope_denominators WHERE scope = 'teams_gt_5'
),
scenario_change_rows AS (
  SELECT 'scenario_comparison' AS row_type, scope || '_groups_changed' AS metric, groups_changed::DECIMAL(18,4) AS metric_value FROM scenario_changes
  UNION ALL SELECT 'scenario_comparison', scope || '_flags_changed', flags_changed::DECIMAL(18,4) FROM scenario_changes
  UNION ALL SELECT 'scenario_comparison', scope || '_employee_snapshots_flagged_exit', employee_snapshots_flagged_exit::DECIMAL(18,4) FROM scenario_changes
  UNION ALL SELECT 'scenario_comparison', scope || '_employee_snapshots_flagged_evaluation', employee_snapshots_flagged_evaluation::DECIMAL(18,4) FROM scenario_changes
),
aggregate_output AS (
  SELECT row_type, CAST(NULL AS VARCHAR(32)) AS scope, CAST(NULL AS VARCHAR(32)) AS attribution,
    CAST(NULL AS DATE) AS snapshot_date, CAST(NULL AS VARCHAR(8)) AS bucket,
    CAST(NULL AS BIGINT) AS team_snapshot_groups, CAST(NULL AS BIGINT) AS employee_snapshots,
    CAST(NULL AS BIGINT) AS total_team_snapshot_groups, CAST(NULL AS BIGINT) AS total_employee_snapshots,
    CAST(NULL AS BIGINT) AS snapshots_checked, CAST(NULL AS DECIMAL(18,4)) AS group_share_percent,
    CAST(NULL AS DECIMAL(18,4)) AS employee_snapshot_share_percent, CAST(NULL AS BIGINT) AS flagged_employees,
    CAST(NULL AS BIGINT) AS observable_employees, CAST(NULL AS DECIMAL(18,6)) AS employee_percent,
    CAST(NULL AS BIGINT) AS affected_teams, metric, metric_value
  FROM audit_rows
  UNION ALL
  SELECT row_type, CAST(NULL AS VARCHAR(32)), CAST(NULL AS VARCHAR(32)), CAST(NULL AS DATE), CAST(NULL AS VARCHAR(8)),
    CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)), CAST(NULL AS DECIMAL(18,4)), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,6)), CAST(NULL AS BIGINT), metric, metric_value
  FROM scenario_change_rows
)
SELECT row_type, scope, attribution, snapshot_date, bucket, team_snapshot_groups, employee_snapshots,
  total_team_snapshot_groups, total_employee_snapshots, snapshots_checked, group_share_percent,
  employee_snapshot_share_percent, flagged_employees, observable_employees, employee_percent,
  affected_teams, metric, metric_value
FROM monthly_output
UNION ALL SELECT row_type, scope, attribution, snapshot_date, bucket, team_snapshot_groups, employee_snapshots,
  total_team_snapshot_groups, total_employee_snapshots, snapshots_checked, group_share_percent,
  employee_snapshot_share_percent, flagged_employees, observable_employees, employee_percent,
  affected_teams, metric, metric_value FROM bucket_output
UNION ALL SELECT row_type, scope, attribution, snapshot_date, bucket, team_snapshot_groups, employee_snapshots,
  total_team_snapshot_groups, total_employee_snapshots, snapshots_checked, group_share_percent,
  employee_snapshot_share_percent, flagged_employees, observable_employees, employee_percent,
  affected_teams, metric, metric_value FROM aggregate_output
ORDER BY row_type, scope, attribution, snapshot_date, bucket, metric;
