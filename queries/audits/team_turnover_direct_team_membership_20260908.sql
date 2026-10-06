-- Claim: a direct-report team can be reconstructed at the 2026-09-07 daily
-- snapshot from manager_employee_id for active regular employees.
-- Semantic type: hierarchy / derived-feature input at employee-day grain.
-- Deliverable mode: internal_analysis. Aggregate-only output.
-- Proposed formal membership at snapshot t:
--   team(m, t) = { employee e : e is active regular at t and
--                  manager_employee_id(e, t) = m }.
-- The manager m is not a member of their own direct-report team. A peer of m
-- is any employee p where manager_employee_id(p, t) = manager_employee_id(m, t).
-- Acceptance rule:
--   1) each active-regular employee has one row at the employee-day grain;
--   2) no self-manager relationships occur; and
--   3) every non-null manager reference resolves once in the same snapshot,
--      except relationships explicitly classified as unresolved/unknown.
WITH active_regular AS (
  SELECT
    employee_id,
    manager_employee_id
  FROM hrda.post_hire_daily_worker_dtls
  WHERE CAST(transaction_date AS DATE) = DATE '2026-09-07'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
employee_rows AS (
  SELECT
    employee_id,
    COUNT(*) AS employee_day_rows
  FROM active_regular
  GROUP BY 1
),
manager_references AS (
  SELECT
    active_regular.employee_id,
    active_regular.manager_employee_id,
    employee_rows.employee_day_rows AS resolved_manager_rows
  FROM active_regular
  LEFT JOIN employee_rows
    ON active_regular.manager_employee_id = employee_rows.employee_id
)
SELECT
  COUNT(*) AS active_regular_employee_day_rows,
  COUNT(DISTINCT employee_id) AS distinct_active_regular_employees,
  SUM(CASE WHEN manager_employee_id IS NULL THEN 1 ELSE 0 END) AS no_manager_employee_rows,
  SUM(CASE WHEN employee_id = manager_employee_id THEN 1 ELSE 0 END) AS self_manager_rows,
  SUM(CASE WHEN manager_employee_id IS NOT NULL AND resolved_manager_rows = 1 THEN 1 ELSE 0 END) AS manager_references_resolved_once,
  SUM(CASE WHEN manager_employee_id IS NOT NULL AND COALESCE(resolved_manager_rows, 0) = 0 THEN 1 ELSE 0 END) AS manager_references_unresolved,
  SUM(CASE WHEN manager_employee_id IS NOT NULL AND resolved_manager_rows > 1 THEN 1 ELSE 0 END) AS manager_references_multi_match
FROM manager_references;
