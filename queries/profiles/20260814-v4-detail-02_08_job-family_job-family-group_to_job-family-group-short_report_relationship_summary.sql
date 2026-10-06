WITH paired AS (
  SELECT
    CAST("job_family_group" AS VARCHAR(512)) AS left_value,
    CAST("job_family_group_short" AS VARCHAR(512)) AS right_value,
    "employee_id" AS employee_key
  FROM "hrda"."post_hire_monthly_worker_dtls"
  WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
    AND "fis_mo_end_dt" = (
      SELECT MAX("fis_mo_end_dt")
      FROM "hrda"."post_hire_monthly_worker_dtls"
      WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
        AND "fis_mo_end_dt" IS NOT NULL
    )
    AND NULLIF(TRIM(CAST("job_family_group" AS VARCHAR)), '') IS NOT NULL
    AND NULLIF(TRIM(CAST("job_family_group_short" AS VARCHAR)), '') IS NOT NULL
), left_many AS (
  SELECT left_value
  FROM paired
  GROUP BY left_value
  HAVING COUNT(DISTINCT right_value) > 1
), right_many AS (
  SELECT right_value
  FROM paired
  GROUP BY right_value
  HAVING COUNT(DISTINCT left_value) > 1
)
SELECT
  'summary' AS row_type,
  'job_family_group -> job_family_group_short' AS pair,
  CAST(NULL AS VARCHAR(512)) AS left_value,
  CAST(NULL AS VARCHAR(512)) AS right_value,
  COUNT(DISTINCT employee_key) AS employee_count,
  COUNT(DISTINCT left_value) AS left_distinct_values,
  COUNT(DISTINCT right_value) AS right_distinct_values,
  (SELECT COUNT(*) FROM left_many) AS left_values_with_multiple_right_values,
  (SELECT COUNT(*) FROM right_many) AS right_values_with_multiple_left_values
FROM paired
