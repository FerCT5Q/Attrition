WITH snapshots AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS VARCHAR(32)) AS fiscal_year,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
linked_employees AS (
  SELECT employee_id
  FROM hrda.applications
  WHERE employee_id IS NOT NULL
  GROUP BY employee_id
),
applied_events AS (
  SELECT
    employee_id,
    application_date,
    req_id
  FROM hrda.applications
  WHERE employee_id IS NOT NULL
    AND application_date IS NOT NULL
    AND cand_applied = 1
  GROUP BY employee_id, application_date, req_id
)
SELECT
  snapshots.snapshot_date,
  snapshots.fiscal_year,
  COUNT(DISTINCT snapshots.employee_id) AS eligible_employees,
  COUNT(DISTINCT CASE
    WHEN linked_employees.employee_id IS NOT NULL THEN snapshots.employee_id
  END) AS observable_employees,
  COUNT(DISTINCT CASE
    WHEN applied_events.application_date > DATEADD(month, -1, snapshots.snapshot_date)
     AND applied_events.application_date <= snapshots.snapshot_date
    THEN snapshots.employee_id
  END) AS event_employees,
  'Application records are deduplicated by employee, date, and requisition.' AS notes
FROM snapshots
LEFT JOIN linked_employees
  ON snapshots.employee_id = linked_employees.employee_id
LEFT JOIN applied_events
  ON snapshots.employee_id = applied_events.employee_id
 AND applied_events.application_date > DATEADD(month, -1, snapshots.snapshot_date)
 AND applied_events.application_date <= snapshots.snapshot_date
GROUP BY snapshots.snapshot_date, snapshots.fiscal_year
ORDER BY snapshots.snapshot_date
