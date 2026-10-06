SELECT
  'top_mapping' AS row_type,
  'et_9_leader -> et_10_leader' AS pair,
  CAST("et_9_leader" AS VARCHAR(512)) AS left_value,
  CAST("et_10_leader" AS VARCHAR(512)) AS right_value,
  COUNT(DISTINCT "employee_id") AS employee_count,
  CAST(NULL AS BIGINT) AS left_distinct_values,
  CAST(NULL AS BIGINT) AS right_distinct_values,
  CAST(NULL AS BIGINT) AS left_values_with_multiple_right_values,
  CAST(NULL AS BIGINT) AS right_values_with_multiple_left_values
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" = (
    SELECT MAX("fis_mo_end_dt")
    FROM "hrda"."post_hire_monthly_worker_dtls"
    WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
      AND "fis_mo_end_dt" IS NOT NULL
  )
  AND NULLIF(TRIM(CAST("et_9_leader" AS VARCHAR)), '') IS NOT NULL
  AND NULLIF(TRIM(CAST("et_10_leader" AS VARCHAR)), '') IS NOT NULL
GROUP BY 1, 2, 3, 4
HAVING COUNT(DISTINCT "employee_id") >= 30
ORDER BY employee_count DESC, left_value, right_value
LIMIT 25
