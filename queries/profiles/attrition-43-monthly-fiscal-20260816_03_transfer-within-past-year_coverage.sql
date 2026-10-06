SELECT
  CAST("fis_mo_end_dt" AS DATE) AS snapshot_date,
  CAST("fiscal_year" AS VARCHAR(32)) AS fiscal_year,
  COUNT(DISTINCT "employee_id") AS eligible_employees,
  COUNT(DISTINCT CASE WHEN (NULLIF(TRIM(CAST("is_transferred" AS VARCHAR)), '') IS NOT NULL) THEN "employee_id" END) AS observable_employees,
  COUNT(DISTINCT CASE WHEN ("is_transferred" > 0) THEN "employee_id" END) AS event_employees
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" IS NOT NULL
GROUP BY 1, 2
HAVING COUNT(DISTINCT "employee_id") >= 30
ORDER BY 1
