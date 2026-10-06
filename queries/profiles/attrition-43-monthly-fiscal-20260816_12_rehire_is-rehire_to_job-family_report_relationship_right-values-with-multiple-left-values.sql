SELECT 'right_values_with_multiple_left_values' AS metric,
       COUNT(*) AS metric_value
FROM (
  SELECT right_value
  FROM (
    SELECT DISTINCT
      CAST("is_rehire" AS VARCHAR(512)) AS left_value,
      CAST("job_family" AS VARCHAR(512)) AS right_value
    FROM "hrda"."post_hire_monthly_worker_dtls"
    WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
    AND "fis_mo_end_dt" = (
      SELECT MAX("fis_mo_end_dt")
      FROM "hrda"."post_hire_monthly_worker_dtls"
      WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
        AND "fis_mo_end_dt" IS NOT NULL
    )
    AND NULLIF(TRIM(CAST("is_rehire" AS VARCHAR)), '') IS NOT NULL
    AND NULLIF(TRIM(CAST("job_family" AS VARCHAR)), '') IS NOT NULL
  ) unique_pairs
  GROUP BY right_value
  HAVING COUNT(*) > 1
) right_many
