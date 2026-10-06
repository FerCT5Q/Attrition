-- Follow-up to team_turnover_direct_team_membership_20260908.sql.
-- Claim: active-regular direct-report references can resolve against the
-- full active worker directory at the same daily snapshot.
-- Why: managers may not themselves satisfy the active-regular employee
-- population filter used for the feature denominator.
-- Acceptance rule: every populated manager_employee_id from the eligible
-- direct-report population resolves exactly once in the same snapshot; any
-- remaining unresolved reference must be treated as Unknown in the feature.
WITH direct_reports AS (
  SELECT
    employee_id,
    manager_employee_id
  FROM hrda.post_hire_daily_worker_dtls
  WHERE CAST(transaction_date AS DATE) = DATE '2026-09-07'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
active_worker_directory AS (
  SELECT
    employee_id,
    COUNT(*) AS active_worker_rows
  FROM hrda.post_hire_daily_worker_dtls
  WHERE CAST(transaction_date AS DATE) = DATE '2026-09-07'
    AND active_status = 1
  GROUP BY 1
),
manager_references AS (
  SELECT
    direct_reports.employee_id,
    direct_reports.manager_employee_id,
    active_worker_directory.active_worker_rows AS resolved_manager_rows
  FROM direct_reports
  LEFT JOIN active_worker_directory
    ON direct_reports.manager_employee_id = active_worker_directory.employee_id
)
SELECT
  COUNT(*) AS direct_report_employee_rows,
  SUM(CASE WHEN manager_employee_id IS NULL THEN 1 ELSE 0 END) AS no_manager_employee_rows,
  SUM(CASE WHEN manager_employee_id IS NOT NULL AND resolved_manager_rows = 1 THEN 1 ELSE 0 END) AS manager_references_resolved_once,
  SUM(CASE WHEN manager_employee_id IS NOT NULL AND COALESCE(resolved_manager_rows, 0) = 0 THEN 1 ELSE 0 END) AS manager_references_unresolved,
  SUM(CASE WHEN manager_employee_id IS NOT NULL AND resolved_manager_rows > 1 THEN 1 ELSE 0 END) AS manager_references_multi_match
FROM manager_references;
