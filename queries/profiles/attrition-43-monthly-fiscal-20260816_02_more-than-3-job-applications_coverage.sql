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
),
employee_month AS (
  SELECT
    snapshots.snapshot_date,
    snapshots.fiscal_year,
    snapshots.employee_id,
    MAX(CASE
      WHEN linked_employees.employee_id IS NOT NULL THEN 1 ELSE 0
    END) AS observable_flag,
    COUNT(DISTINCT CASE
      WHEN applied_events.application_date > DATEADD(month, -12, snapshots.snapshot_date)
       AND applied_events.application_date <= snapshots.snapshot_date
      THEN applied_events.req_id
    END) AS trailing_applications
  FROM snapshots
  LEFT JOIN linked_employees
    ON snapshots.employee_id = linked_employees.employee_id
  LEFT JOIN applied_events
    ON snapshots.employee_id = applied_events.employee_id
   AND applied_events.application_date > DATEADD(month, -12, snapshots.snapshot_date)
   AND applied_events.application_date <= snapshots.snapshot_date
  GROUP BY snapshots.snapshot_date, snapshots.fiscal_year, snapshots.employee_id
)
SELECT
  snapshot_date,
  fiscal_year,
  COUNT(*) AS eligible_employees,
  SUM(observable_flag) AS observable_employees,
  SUM(CASE WHEN trailing_applications > 3 THEN 1 ELSE 0 END) AS event_employees,
  'Event means more than three deduplicated requisitions in the trailing 12 months.' AS notes
FROM employee_month
GROUP BY snapshot_date, fiscal_year
ORDER BY snapshot_date
