SELECT
  CAST("fis_mo_end_dt" AS DATE) AS snapshot_date,
  CAST("fiscal_year" AS VARCHAR(32)) AS fiscal_year,
  COUNT(DISTINCT "employee_id") AS eligible_employees,
  COUNT(DISTINCT CASE WHEN (NULLIF(TRIM(CAST("et_1_leader" AS VARCHAR)), '') IS NOT NULL OR NULLIF(TRIM(CAST("et_2_leader" AS VARCHAR)), '') IS NOT NULL OR NULLIF(TRIM(CAST("et_3_leader" AS VARCHAR)), '') IS NOT NULL OR NULLIF(TRIM(CAST("et_4_leader" AS VARCHAR)), '') IS NOT NULL OR NULLIF(TRIM(CAST("et_5_leader" AS VARCHAR)), '') IS NOT NULL OR NULLIF(TRIM(CAST("et_6_leader" AS VARCHAR)), '') IS NOT NULL OR NULLIF(TRIM(CAST("et_7_leader" AS VARCHAR)), '') IS NOT NULL OR NULLIF(TRIM(CAST("et_8_leader" AS VARCHAR)), '') IS NOT NULL OR NULLIF(TRIM(CAST("et_9_leader" AS VARCHAR)), '') IS NOT NULL OR NULLIF(TRIM(CAST("et_10_leader" AS VARCHAR)), '') IS NOT NULL OR NULLIF(TRIM(CAST("et_11_leader" AS VARCHAR)), '') IS NOT NULL) THEN "employee_id" END) AS observable_employees,
  CAST(NULL AS BIGINT) AS event_employees
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" IS NOT NULL
GROUP BY 1, 2
HAVING COUNT(DISTINCT "employee_id") >= 30
ORDER BY 1
