-- Claim: Team turnover can be reported as two aggregate, time-safe scenarios
-- at the manager-team grain using a six-month retrospective window.
-- Semantic type: derived feature.
-- Definition at cutoff t = 2026-08-23:
--   direct_team(m, s) = active regular employees e with
--                       manager_employee_id(e, s) = m at monthly snapshot s.
--   voluntary exit = term_type exactly 'Voluntary'; 'Voluntary Exception' is
--                    excluded pending authoritative HR treatment.
--   exit attribution = the employee's last active-regular manager snapshot
--                      with fis_mo_end_dt <= term_date.
-- Scenarios are selected from the current direct-team size at t:
--   All manager-led teams: team_size_at_t >= 1.
--   Teams with >5 direct reports: team_size_at_t >= 6.
-- Metric: voluntary exits per 100 direct-report employee-months in the
-- six-month window. This is a cohort-level exposure rate, not a manager label.
-- Acceptance rule:
--   1) six monthly snapshots occur in the window;
--   2) each scenario contains at least 30 manager teams;
--   3) every displayed team has direct-report exposure; and
--   4) only exits attributable to a pre-exit manager snapshot enter the rate.
WITH parameters AS (
  SELECT
    DATE '2026-08-23' AS cutoff_date,
    DATEADD(month, -6, DATE '2026-08-23') AS window_start
),
monthly_membership AS (
  SELECT
    CAST(worker.fis_mo_end_dt AS DATE) AS snapshot_date,
    worker.employee_id,
    worker.manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls AS worker
  CROSS JOIN parameters
  WHERE CAST(worker.fis_mo_end_dt AS DATE) > parameters.window_start
    AND CAST(worker.fis_mo_end_dt AS DATE) <= parameters.cutoff_date
    AND worker.worker_type = 'Employee'
    AND worker.employee_type = 'Regular'
    AND worker.active_status = 1
    AND worker.manager_employee_id IS NOT NULL
),
window_snapshots AS (
  SELECT COUNT(DISTINCT snapshot_date) AS monthly_snapshot_count
  FROM monthly_membership
),
current_team_sizes AS (
  SELECT
    manager_employee_id,
    COUNT(DISTINCT employee_id) AS direct_reports_at_cutoff
  FROM monthly_membership
  CROSS JOIN parameters
  WHERE snapshot_date = parameters.cutoff_date
  GROUP BY 1
),
scenarios AS (
  SELECT 'All manager-led teams' AS scenario, 1 AS minimum_direct_reports
  UNION ALL
  SELECT 'Teams with >5 direct reports' AS scenario, 6 AS minimum_direct_reports
),
scenario_teams AS (
  SELECT
    scenarios.scenario,
    current_team_sizes.manager_employee_id,
    current_team_sizes.direct_reports_at_cutoff
  FROM scenarios
  INNER JOIN current_team_sizes
    ON current_team_sizes.direct_reports_at_cutoff >= scenarios.minimum_direct_reports
),
team_exposure AS (
  SELECT
    scenario_teams.scenario,
    scenario_teams.manager_employee_id,
    scenario_teams.direct_reports_at_cutoff,
    COUNT(DISTINCT monthly_membership.employee_id || '|' || monthly_membership.snapshot_date::VARCHAR) AS employee_months
  FROM scenario_teams
  INNER JOIN monthly_membership
    ON monthly_membership.manager_employee_id = scenario_teams.manager_employee_id
  GROUP BY 1, 2, 3
),
voluntary_termination_events AS (
  SELECT
    worker.employee_id,
    worker.term_date
  FROM hrda.post_hire_monthly_worker_dtls AS worker
  CROSS JOIN parameters
  WHERE worker.term_date > parameters.window_start
    AND worker.term_date <= parameters.cutoff_date
    AND UPPER(NULLIF(TRIM(CAST(worker.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
),
manager_history_candidates AS (
  SELECT
    voluntary_termination_events.employee_id,
    voluntary_termination_events.term_date,
    history.manager_employee_id,
    CAST(history.fis_mo_end_dt AS DATE) AS manager_snapshot_date,
    ROW_NUMBER() OVER (
      PARTITION BY voluntary_termination_events.employee_id, voluntary_termination_events.term_date
      ORDER BY CAST(history.fis_mo_end_dt AS DATE) DESC
    ) AS manager_snapshot_rank
  FROM voluntary_termination_events
  LEFT JOIN hrda.post_hire_monthly_worker_dtls AS history
    ON history.employee_id = voluntary_termination_events.employee_id
    AND history.worker_type = 'Employee'
    AND history.employee_type = 'Regular'
    AND history.active_status = 1
    AND history.manager_employee_id IS NOT NULL
    AND CAST(history.fis_mo_end_dt AS DATE) <= voluntary_termination_events.term_date
    AND CAST(history.fis_mo_end_dt AS DATE) >= DATEADD(month, -1, DATE '2026-02-23')
),
attributed_voluntary_exits AS (
  SELECT
    employee_id,
    term_date,
    manager_employee_id
  FROM manager_history_candidates
  WHERE manager_snapshot_rank = 1
    AND manager_employee_id IS NOT NULL
),
voluntary_exits_by_manager AS (
  SELECT
    manager_employee_id,
    COUNT(*) AS voluntary_exit_events
  FROM attributed_voluntary_exits
  GROUP BY 1
),
scenario_rates AS (
  SELECT
    team_exposure.scenario,
    COUNT(*) AS manager_teams,
    SUM(team_exposure.direct_reports_at_cutoff) AS direct_reports_at_cutoff,
    SUM(team_exposure.employee_months) AS employee_months,
    SUM(COALESCE(voluntary_exits_by_manager.voluntary_exit_events, 0)) AS voluntary_exit_events,
    SUM(CASE WHEN COALESCE(voluntary_exits_by_manager.voluntary_exit_events, 0) = 0 THEN 1 ELSE 0 END) AS teams_without_voluntary_exit,
    SUM(CASE WHEN COALESCE(voluntary_exits_by_manager.voluntary_exit_events, 0) > 0 THEN 1 ELSE 0 END) AS teams_with_at_least_one_voluntary_exit
  FROM team_exposure
  LEFT JOIN voluntary_exits_by_manager
    ON voluntary_exits_by_manager.manager_employee_id = team_exposure.manager_employee_id
  GROUP BY 1
)
SELECT
  'scenario_summary' AS row_type,
  scenario_rates.scenario,
  parameters.cutoff_date,
  parameters.window_start,
  window_snapshots.monthly_snapshot_count,
  scenario_rates.manager_teams,
  scenario_rates.direct_reports_at_cutoff,
  scenario_rates.employee_months,
  scenario_rates.voluntary_exit_events,
  scenario_rates.teams_without_voluntary_exit,
  scenario_rates.teams_with_at_least_one_voluntary_exit,
  ROUND(100.0 * scenario_rates.voluntary_exit_events / NULLIF(scenario_rates.employee_months, 0), 4) AS voluntary_exits_per_100_employee_months,
  ROUND(100.0 * scenario_rates.voluntary_exit_events * window_snapshots.monthly_snapshot_count / NULLIF(scenario_rates.employee_months, 0), 4) AS six_month_turnover_percent,
  CAST(NULL AS BIGINT) AS total_voluntary_termination_events,
  CAST(NULL AS BIGINT) AS attributed_voluntary_termination_events
FROM scenario_rates
CROSS JOIN parameters
CROSS JOIN window_snapshots

UNION ALL

SELECT
  'attribution_summary' AS row_type,
  'Strict Voluntary term_type only' AS scenario,
  parameters.cutoff_date,
  parameters.window_start,
  window_snapshots.monthly_snapshot_count,
  CAST(NULL AS BIGINT) AS manager_teams,
  CAST(NULL AS BIGINT) AS direct_reports_at_cutoff,
  CAST(NULL AS BIGINT) AS employee_months,
  CAST(NULL AS BIGINT) AS voluntary_exit_events,
  CAST(NULL AS BIGINT) AS teams_without_voluntary_exit,
  CAST(NULL AS BIGINT) AS teams_with_at_least_one_voluntary_exit,
  CAST(NULL AS DECIMAL(18, 4)) AS voluntary_exits_per_100_employee_months,
  CAST(NULL AS DECIMAL(18, 4)) AS six_month_turnover_percent,
  COUNT(*) AS total_voluntary_termination_events,
  SUM(CASE WHEN attributed_voluntary_exits.manager_employee_id IS NOT NULL THEN 1 ELSE 0 END) AS attributed_voluntary_termination_events
FROM voluntary_termination_events
LEFT JOIN attributed_voluntary_exits
  ON attributed_voluntary_exits.employee_id = voluntary_termination_events.employee_id
  AND attributed_voluntary_exits.term_date = voluntary_termination_events.term_date
CROSS JOIN parameters
CROSS JOIN window_snapshots
GROUP BY
  parameters.cutoff_date,
  parameters.window_start,
  window_snapshots.monthly_snapshot_count
ORDER BY row_type, scenario;
