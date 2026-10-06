SELECT 'left_values_with_multiple_right_values' AS metric,
       COUNT(*) AS metric_value
FROM (
  SELECT left_value
  FROM (
    SELECT DISTINCT
      CAST("active_status" AS VARCHAR(512)) AS left_value,
      CAST("is_termed" AS VARCHAR(512)) AS right_value
    FROM "hrda"."post_hire_monthly_worker_dtls"
    WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
    AND "fis_mo_end_dt" = (
      SELECT MAX("fis_mo_end_dt")
      FROM "hrda"."post_hire_monthly_worker_dtls"
      WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
        AND "fis_mo_end_dt" IS NOT NULL
    )
    AND NULLIF(TRIM(CAST("active_status" AS VARCHAR)), '') IS NOT NULL
    AND NULLIF(TRIM(CAST("is_termed" AS VARCHAR)), '') IS NOT NULL
  ) unique_pairs
  GROUP BY left_value
  HAVING COUNT(*) > 1
) left_many
