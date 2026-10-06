SELECT 'employee_count' AS metric,
       COUNT(DISTINCT "employee_id") AS metric_value
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
    AND "fis_mo_end_dt" = (
      SELECT MAX("fis_mo_end_dt")
      FROM "hrda"."post_hire_monthly_worker_dtls"
      WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
        AND "fis_mo_end_dt" IS NOT NULL
    )
    AND NULLIF(TRIM(CAST("worker_type" AS VARCHAR)), '') IS NOT NULL
    AND NULLIF(TRIM(CAST("employee_type" AS VARCHAR)), '') IS NOT NULL
