-- Claim: annual supplementary comparison for the time-safe team-exit exposure
-- feature. It uses the same employee-snapshot population, scopes, event rule,
-- and attribution alternatives as the six-month primary series, but the event
-- window is (t - 12 months, t].
-- Deliverable mode: internal_analysis; aggregate-only output.
--
-- Acceptance rule:
--   * every valid evaluation point has exactly 12 monthly snapshots;
--   * flagged_employees <= observable_employees and the denominator is >= 30;
--   * no duplicate active regular employee-snapshot membership rows;
--   * only exact normalized Voluntary events enter the numerator.

WITH
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
  SELECT snapshot_date
  FROM raw_monthly
  GROUP BY 1
),
valid_evaluation_snapshots AS (
  SELECT
    evaluation_candidate.snapshot_date,
    COUNT(DISTINCT history.snapshot_date) AS window_snapshot_count,
    MIN(history.snapshot_date) AS earliest_snapshot_in_window,
    MAX(history.snapshot_date) AS latest_snapshot_in_window
  FROM snapshot_dates AS evaluation_candidate
  LEFT JOIN snapshot_dates AS history
    ON history.snapshot_date > DATEADD(month, -12, evaluation_candidate.snapshot_date)
   AND history.snapshot_date <= evaluation_candidate.snapshot_date
  GROUP BY 1
  HAVING COUNT(DISTINCT history.snapshot_date) >= 12
     AND DATEDIFF(day, MIN(history.snapshot_date), MAX(history.snapshot_date)) >= 330
),
membership AS (
  SELECT monthly.snapshot_date, monthly.employee_id, monthly.manager_employee_id
  FROM raw_monthly AS monthly
  INNER JOIN valid_evaluation_snapshots AS evaluation
    ON evaluation.snapshot_date = monthly.snapshot_date
  WHERE monthly.manager_employee_id IS NOT NULL
),
team_sizes AS (
  SELECT
    snapshot_date,
    manager_employee_id,
    COUNT(DISTINCT employee_id) AS direct_reports
  FROM membership
  GROUP BY 1, 2
),
scopes AS (
  SELECT 'all_teams' AS scope, 1 AS minimum_direct_reports
  UNION ALL
  SELECT 'teams_gt_5' AS scope, 6 AS minimum_direct_reports
),
team_snapshot_groups AS (
  SELECT scope.scope, teams.snapshot_date, teams.manager_employee_id, teams.direct_reports
  FROM team_sizes AS teams
  CROSS JOIN scopes AS scope
  WHERE teams.direct_reports >= scope.minimum_direct_reports
),
scope_employee_rows AS (
  SELECT DISTINCT
    groups.scope,
    groups.snapshot_date,
    member.employee_id,
    member.manager_employee_id
  FROM team_snapshot_groups AS groups
  INNER JOIN membership AS member
    ON member.snapshot_date = groups.snapshot_date
   AND member.manager_employee_id = groups.manager_employee_id
),
voluntary_events AS (
  SELECT
    worker.employee_id,
    CAST(worker.term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls AS worker
  CROSS JOIN parameters
  WHERE CAST(worker.term_date AS DATE) <= parameters.cutoff_date
    AND CAST(worker.term_date AS DATE) > DATEADD(
      month,
      -12,
      (SELECT MIN(snapshot_date) FROM valid_evaluation_snapshots)
    )
    AND UPPER(NULLIF(TRIM(CAST(worker.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
),
manager_at_exit_candidates AS (
  SELECT
    event.employee_id,
    event.term_date,
    history.manager_employee_id,
    ROW_NUMBER() OVER (
      PARTITION BY event.employee_id, event.term_date
      ORDER BY history.snapshot_date DESC, history.manager_employee_id
    ) AS manager_rank
  FROM voluntary_events AS event
  LEFT JOIN raw_monthly AS history
    ON history.employee_id = event.employee_id
   AND history.manager_employee_id IS NOT NULL
   AND history.snapshot_date <= event.term_date
),
manager_at_exit AS (
  SELECT employee_id, term_date, manager_employee_id
  FROM manager_at_exit_candidates
  WHERE manager_rank = 1
    AND manager_employee_id IS NOT NULL
),
manager_at_evaluation_candidates AS (
  SELECT
    event.employee_id,
    event.term_date,
    evaluation.snapshot_date,
    history.manager_employee_id,
    ROW_NUMBER() OVER (
      PARTITION BY event.employee_id, event.term_date, evaluation.snapshot_date
      ORDER BY history.snapshot_date DESC, history.manager_employee_id
    ) AS manager_rank
  FROM voluntary_events AS event
  INNER JOIN valid_evaluation_snapshots AS evaluation
    ON event.term_date <= evaluation.snapshot_date
   AND event.term_date > DATEADD(month, -12, evaluation.snapshot_date)
  LEFT JOIN raw_monthly AS history
    ON history.employee_id = event.employee_id
   AND history.manager_employee_id IS NOT NULL
   AND history.snapshot_date <= evaluation.snapshot_date
),
manager_at_evaluation AS (
  SELECT employee_id, term_date, snapshot_date, manager_employee_id
  FROM manager_at_evaluation_candidates
  WHERE manager_rank = 1
    AND manager_employee_id IS NOT NULL
),
manager_exit_counts AS (
  SELECT
    groups.scope,
    groups.snapshot_date,
    groups.manager_employee_id,
    COUNT(DISTINCT CASE
      WHEN event.term_date > DATEADD(month, -12, groups.snapshot_date)
       AND event.term_date <= groups.snapshot_date
      THEN event.employee_id || '|' || event.term_date::VARCHAR
    END) AS exit_count
  FROM team_snapshot_groups AS groups
  LEFT JOIN manager_at_exit AS event
    ON event.manager_employee_id = groups.manager_employee_id
  GROUP BY 1, 2, 3
),
manager_evaluation_counts AS (
  SELECT
    groups.scope,
    groups.snapshot_date,
    groups.manager_employee_id,
    COUNT(DISTINCT CASE
      WHEN event.snapshot_date = groups.snapshot_date
      THEN event.employee_id || '|' || event.term_date::VARCHAR
    END) AS exit_count
  FROM team_snapshot_groups AS groups
  LEFT JOIN manager_at_evaluation AS event
    ON event.snapshot_date = groups.snapshot_date
   AND event.manager_employee_id = groups.manager_employee_id
  GROUP BY 1, 2, 3
),
monthly_series AS (
  SELECT
    employee.scope,
    'manager_at_exit' AS attribution,
    employee.snapshot_date,
    COUNT(DISTINCT CASE WHEN counts.exit_count >= 2 THEN employee.employee_id END) AS flagged_employees,
    COUNT(DISTINCT employee.employee_id) AS observable_employees,
    COUNT(DISTINCT CASE WHEN counts.exit_count >= 2 THEN employee.manager_employee_id END) AS affected_teams
  FROM scope_employee_rows AS employee
  INNER JOIN manager_exit_counts AS counts
    ON counts.scope = employee.scope
   AND counts.snapshot_date = employee.snapshot_date
   AND counts.manager_employee_id = employee.manager_employee_id
  GROUP BY 1, 2, 3
  UNION ALL
  SELECT
    employee.scope,
    'manager_at_evaluation' AS attribution,
    employee.snapshot_date,
    COUNT(DISTINCT CASE WHEN counts.exit_count >= 2 THEN employee.employee_id END) AS flagged_employees,
    COUNT(DISTINCT employee.employee_id) AS observable_employees,
    COUNT(DISTINCT CASE WHEN counts.exit_count >= 2 THEN employee.manager_employee_id END) AS affected_teams
  FROM scope_employee_rows AS employee
  INNER JOIN manager_evaluation_counts AS counts
    ON counts.scope = employee.scope
   AND counts.snapshot_date = employee.snapshot_date
   AND counts.manager_employee_id = employee.manager_employee_id
  GROUP BY 1, 2, 3
),
monthly_output AS (
  SELECT
    'monthly_series' AS row_type,
    series.scope,
    series.attribution,
    series.snapshot_date,
    series.flagged_employees,
    series.observable_employees,
    ROUND(100.0 * series.flagged_employees / NULLIF(series.observable_employees, 0), 6) AS employee_percent,
    series.affected_teams,
    CAST(NULL AS VARCHAR(128)) AS metric,
    CAST(NULL AS DECIMAL(18,4)) AS metric_value
  FROM monthly_series AS series
),
audit_rows AS (
  SELECT 'window_snapshot_count_min' AS metric, MIN(window_snapshot_count)::DECIMAL(18,4) AS metric_value
  FROM valid_evaluation_snapshots
  UNION ALL
  SELECT 'window_snapshot_count_max', MAX(window_snapshot_count)::DECIMAL(18,4)
  FROM valid_evaluation_snapshots
  UNION ALL
  SELECT 'evaluation_snapshots', COUNT(*)::DECIMAL(18,4)
  FROM valid_evaluation_snapshots
  UNION ALL
  SELECT 'monthly_series_points', COUNT(*)::DECIMAL(18,4)
  FROM monthly_series
  UNION ALL
  SELECT 'monthly_series_numerator_over_denominator',
    SUM(CASE WHEN flagged_employees > observable_employees THEN 1 ELSE 0 END)::DECIMAL(18,4)
  FROM monthly_series
  UNION ALL
  SELECT 'monthly_series_denominator_below_30',
    SUM(CASE WHEN observable_employees < 30 THEN 1 ELSE 0 END)::DECIMAL(18,4)
  FROM monthly_series
  UNION ALL
  SELECT 'membership_duplicate_rows',
    SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END)::DECIMAL(18,4)
  FROM (
    SELECT snapshot_date, employee_id, COUNT(*) AS row_count
    FROM raw_monthly_rows
    GROUP BY 1, 2
  ) AS duplicate_membership
  UNION ALL
  SELECT 'voluntary_events', COUNT(*)::DECIMAL(18,4)
  FROM voluntary_events
  UNION ALL
  SELECT 'voluntary_events_with_manager_at_exit', COUNT(*)::DECIMAL(18,4)
  FROM (
    SELECT DISTINCT employee_id, term_date
    FROM manager_at_exit
  ) AS attributed_events
  UNION ALL
  SELECT 'voluntary_events_unmatched_at_exit', COUNT(*)::DECIMAL(18,4)
  FROM voluntary_events AS event
  LEFT JOIN manager_at_exit AS assigned
    ON assigned.employee_id = event.employee_id
   AND assigned.term_date = event.term_date
  WHERE assigned.employee_id IS NULL
),
audit_output AS (
  SELECT
    'audit' AS row_type,
    CAST(NULL AS VARCHAR(32)) AS scope,
    CAST(NULL AS VARCHAR(32)) AS attribution,
    CAST(NULL AS DATE) AS snapshot_date,
    CAST(NULL AS BIGINT) AS flagged_employees,
    CAST(NULL AS BIGINT) AS observable_employees,
    CAST(NULL AS DECIMAL(18,6)) AS employee_percent,
    CAST(NULL AS BIGINT) AS affected_teams,
    metric,
    metric_value
  FROM audit_rows
)
SELECT
  row_type,
  scope,
  attribution,
  snapshot_date,
  flagged_employees,
  observable_employees,
  employee_percent,
  affected_teams,
  metric,
  metric_value
FROM monthly_output
UNION ALL
SELECT
  row_type,
  scope,
  attribution,
  snapshot_date,
  flagged_employees,
  observable_employees,
  employee_percent,
  affected_teams,
  metric,
  metric_value
FROM audit_output
ORDER BY row_type, scope, attribution, snapshot_date, metric;
