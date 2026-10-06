SELECT 'right_distinct_values' AS metric,
       COUNT(DISTINCT CAST("management_level" AS VARCHAR(512))) AS metric_value
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
    AND "fis_mo_end_dt" = (
      SELECT MAX("fis_mo_end_dt")
      FROM "hrda"."post_hire_monthly_worker_dtls"
      WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
        AND "fis_mo_end_dt" IS NOT NULL
    )
    AND NULLIF(TRIM(CAST("job_level_primary_position" AS VARCHAR)), '') IS NOT NULL
    AND NULLIF(TRIM(CAST("management_level" AS VARCHAR)), '') IS NOT NULL
