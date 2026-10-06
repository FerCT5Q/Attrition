WITH base AS (
SELECT
  'is_transferred' AS column_name,
  CAST("is_transferred" AS VARCHAR(512)) AS value_label,
  COUNT(DISTINCT "employee_id") AS employee_count,
  COUNT(*) AS row_count
FROM "hrda"."post_hire_monthly_worker_dtls" source_rows
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" = (
    SELECT MAX("fis_mo_end_dt")
    FROM "hrda"."post_hire_monthly_worker_dtls" latest_rows
    WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
      AND "fis_mo_end_dt" IS NOT NULL
  )
  AND NULLIF(TRIM(CAST("is_transferred" AS VARCHAR)), '') IS NOT NULL
GROUP BY 1, 2
HAVING COUNT(DISTINCT "employee_id") >= 30
), ranked AS (
  SELECT
    column_name,
    value_label,
    employee_count,
    row_count,
    ROW_NUMBER() OVER (PARTITION BY column_name ORDER BY employee_count DESC, value_label) AS rn
  FROM base
)
SELECT column_name, value_label, employee_count, row_count, rn
FROM ranked
WHERE rn <= 25
ORDER BY column_name, rn
