SELECT
  'job_family' AS column_name,
  CAST("job_family" AS VARCHAR(512)) AS value_label,
  COUNT(DISTINCT "employee_id") AS employee_count,
  COUNT(*) AS row_count
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" = (
    SELECT MAX("fis_mo_end_dt")
    FROM "hrda"."post_hire_monthly_worker_dtls"
    WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
      AND "fis_mo_end_dt" IS NOT NULL
  )
  AND NULLIF(TRIM(CAST("job_family" AS VARCHAR)), '') IS NOT NULL
GROUP BY 1, 2
HAVING COUNT(DISTINCT "employee_id") >= 30
ORDER BY employee_count DESC, value_label
LIMIT 25
