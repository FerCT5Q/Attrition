WITH target AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS VARCHAR(32)) AS fiscal_year,
    employee_id,
    manager_employee_id,
    region,
    job_family_group,
    level_grouped,
    COALESCE(max_hire_rehire_date, service_date, original_hire_date) AS tenure_start_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
)
SELECT
  snapshot_date,
  MAX(fiscal_year) AS fiscal_year,
  COUNT(DISTINCT employee_id) AS eligible_count,
  COUNT(DISTINCT CASE WHEN manager_employee_id IS NOT NULL THEN employee_id END) AS manager_count,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(region), '') IS NOT NULL THEN employee_id END) AS region_count,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(job_family_group), '') IS NOT NULL THEN employee_id END) AS job_family_count,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(level_grouped), '') IS NOT NULL THEN employee_id END) AS level_count,
  COUNT(DISTINCT CASE WHEN tenure_start_date IS NOT NULL AND tenure_start_date <= snapshot_date THEN employee_id END) AS tenure_count,
  COUNT(DISTINCT CASE
    WHEN manager_employee_id IS NOT NULL
     AND NULLIF(TRIM(region), '') IS NOT NULL
     AND NULLIF(TRIM(job_family_group), '') IS NOT NULL
     AND NULLIF(TRIM(level_grouped), '') IS NOT NULL
     AND tenure_start_date IS NOT NULL
     AND tenure_start_date <= snapshot_date
    THEN employee_id
  END) AS all_inputs_count
FROM target
GROUP BY snapshot_date
ORDER BY snapshot_date;
