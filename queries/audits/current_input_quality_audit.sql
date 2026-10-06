WITH latest AS (
  SELECT MAX(fis_mo_end_dt) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
employees AS (
  SELECT
    workers.employee_id,
    workers.manager_employee_id,
    workers.compa_ratio,
    workers.prior_qc_work_years,
    workers.work_arrangement,
    workers.office_site
  FROM hrda.post_hire_monthly_worker_dtls workers
  JOIN latest
    ON workers.fis_mo_end_dt = latest.snapshot_date
  WHERE workers.worker_type = 'Employee'
    AND workers.employee_type = 'Regular'
    AND workers.active_status = 1
),
managers AS (
  SELECT
    workers.employee_id,
    MAX(workers.office_site) AS office_site
  FROM hrda.post_hire_monthly_worker_dtls workers
  JOIN latest
    ON workers.fis_mo_end_dt = latest.snapshot_date
  WHERE workers.worker_type = 'Employee'
    AND workers.employee_type = 'Regular'
    AND workers.active_status = 1
  GROUP BY workers.employee_id
)
SELECT
  COUNT(DISTINCT employees.employee_id) AS eligible_employees,
  COUNT(DISTINCT CASE
    WHEN employees.compa_ratio IS NOT NULL THEN employees.employee_id
  END) AS compa_ratio_populated_employees,
  COUNT(DISTINCT CASE
    WHEN employees.compa_ratio <= 0 THEN employees.employee_id
  END) AS compa_ratio_nonpositive_employees,
  COUNT(DISTINCT CASE
    WHEN employees.compa_ratio > 3 THEN employees.employee_id
  END) AS compa_ratio_above_three_employees,
  COUNT(DISTINCT CASE
    WHEN employees.prior_qc_work_years IS NOT NULL THEN employees.employee_id
  END) AS prior_experience_populated_employees,
  COUNT(DISTINCT CASE
    WHEN employees.prior_qc_work_years < 0 THEN employees.employee_id
  END) AS prior_experience_negative_employees,
  COUNT(DISTINCT CASE
    WHEN employees.prior_qc_work_years > 80 THEN employees.employee_id
  END) AS prior_experience_above_eighty_employees,
  COUNT(DISTINCT CASE
    WHEN NULLIF(TRIM(employees.work_arrangement), '') IS NOT NULL
    THEN employees.work_arrangement
  END) AS work_arrangement_raw_distinct_count,
  COUNT(DISTINCT CASE
    WHEN NULLIF(TRIM(employees.work_arrangement), '') IS NOT NULL
    THEN UPPER(TRIM(employees.work_arrangement))
  END) AS work_arrangement_normalized_distinct_count,
  SUM(CASE
    WHEN employees.work_arrangement IS NOT NULL
     AND employees.work_arrangement <> TRIM(employees.work_arrangement)
    THEN 1 ELSE 0
  END) AS work_arrangement_whitespace_rows,
  COUNT(DISTINCT CASE
    WHEN managers.employee_id IS NOT NULL THEN employees.employee_id
  END) AS matched_manager_employees,
  COUNT(DISTINCT CASE
    WHEN NULLIF(TRIM(employees.office_site), '') IS NOT NULL
     AND NULLIF(TRIM(managers.office_site), '') IS NOT NULL
    THEN employees.employee_id
  END) AS colocation_observable_employees
FROM employees
LEFT JOIN managers
  ON employees.manager_employee_id = managers.employee_id
