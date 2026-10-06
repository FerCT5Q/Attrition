WITH employees AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS VARCHAR(32)) AS fiscal_year,
    employee_id,
    manager_employee_id,
    office_site
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
managers AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    MAX(office_site) AS office_site
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY fis_mo_end_dt, employee_id
)
SELECT
  employees.snapshot_date,
  MAX(employees.fiscal_year) AS fiscal_year,
  COUNT(DISTINCT employees.employee_id) AS eligible_employees,
  COUNT(DISTINCT CASE
    WHEN NULLIF(TRIM(employees.office_site), '') IS NOT NULL
     AND NULLIF(TRIM(managers.office_site), '') IS NOT NULL
    THEN employees.employee_id
  END) AS observable_employees,
  COUNT(DISTINCT CASE
    WHEN NULLIF(TRIM(employees.office_site), '') IS NOT NULL
     AND NULLIF(TRIM(managers.office_site), '') IS NOT NULL
     AND employees.office_site = managers.office_site
    THEN employees.employee_id
  END) AS event_employees,
  'Event means employee and active manager have the same nonblank office site.' AS notes
FROM employees
LEFT JOIN managers
  ON employees.snapshot_date = managers.snapshot_date
 AND employees.manager_employee_id = managers.employee_id
GROUP BY employees.snapshot_date
ORDER BY employees.snapshot_date
