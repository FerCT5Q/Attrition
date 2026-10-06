WITH pair_1 AS (
  SELECT
    CAST("country" AS VARCHAR(512)) AS left_value,
    CAST("office_site" AS VARCHAR(512)) AS right_value,
    "employee_id" AS employee_key
  FROM "hrda"."post_hire_monthly_worker_dtls"
  WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
    AND "fis_mo_end_dt" = (
      SELECT MAX("fis_mo_end_dt")
      FROM "hrda"."post_hire_monthly_worker_dtls"
      WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
        AND "fis_mo_end_dt" IS NOT NULL
    )
    AND NULLIF(TRIM(CAST("country" AS VARCHAR)), '') IS NOT NULL
    AND NULLIF(TRIM(CAST("office_site" AS VARCHAR)), '') IS NOT NULL
),
pair_1_summary AS (
  SELECT
    'country -> office_site' AS pair,
    COUNT(DISTINCT employee_key) AS paired_employees,
    COUNT(DISTINCT left_value) AS left_distinct_values,
    COUNT(DISTINCT right_value) AS right_distinct_values,
    (SELECT COUNT(*) FROM (SELECT left_value FROM pair_1 GROUP BY left_value HAVING COUNT(DISTINCT right_value) > 1) s) AS left_values_with_multiple_right_values,
    (SELECT COUNT(*) FROM (SELECT right_value FROM pair_1 GROUP BY right_value HAVING COUNT(DISTINCT left_value) > 1) s) AS right_values_with_multiple_left_values
  FROM pair_1
),
pair_1_top AS (
  SELECT
    'country -> office_site' AS pair,
    left_value,
    right_value,
    COUNT(DISTINCT employee_key) AS employee_count,
    ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT employee_key) DESC, left_value, right_value) AS rn
  FROM pair_1
  GROUP BY 1, 2, 3
  HAVING COUNT(DISTINCT employee_key) >= 30
)
SELECT 'summary' AS row_type, pair, CAST(NULL AS VARCHAR(512)) AS left_value, CAST(NULL AS VARCHAR(512)) AS right_value,
       paired_employees AS employee_count, left_distinct_values, right_distinct_values,
       left_values_with_multiple_right_values, right_values_with_multiple_left_values
FROM (SELECT * FROM pair_1_summary) summaries
UNION ALL
SELECT 'top_mapping' AS row_type, pair, left_value, right_value, employee_count,
       CAST(NULL AS BIGINT) AS left_distinct_values, CAST(NULL AS BIGINT) AS right_distinct_values,
       CAST(NULL AS BIGINT) AS left_values_with_multiple_right_values, CAST(NULL AS BIGINT) AS right_values_with_multiple_left_values
FROM (SELECT pair, left_value, right_value, employee_count FROM pair_1_top WHERE rn <= 25) mappings
ORDER BY row_type, pair, employee_count DESC
