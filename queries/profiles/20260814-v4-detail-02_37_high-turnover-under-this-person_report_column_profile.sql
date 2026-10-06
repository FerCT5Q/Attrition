SELECT
  'manager_employee_id' AS column_name,
  COUNT(*) AS eligible_rows,
  COUNT(DISTINCT "employee_id") AS eligible_employees,
  SUM(CASE WHEN NULLIF(TRIM(CAST("manager_employee_id" AS VARCHAR)), '') IS NOT NULL THEN 1 ELSE 0 END) AS populated_rows,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(CAST("manager_employee_id" AS VARCHAR)), '') IS NOT NULL THEN "employee_id" END) AS populated_employees,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(CAST("manager_employee_id" AS VARCHAR)), '') IS NOT NULL THEN CAST("manager_employee_id" AS VARCHAR(512)) END) AS distinct_values,
  MIN(CASE WHEN NULLIF(TRIM(CAST("manager_employee_id" AS VARCHAR)), '') IS NOT NULL THEN CAST("fis_mo_end_dt" AS DATE) END) AS first_populated_date,
  MAX(CASE WHEN NULLIF(TRIM(CAST("manager_employee_id" AS VARCHAR)), '') IS NOT NULL THEN CAST("fis_mo_end_dt" AS DATE) END) AS latest_populated_date
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" IS NOT NULL
UNION ALL
SELECT
  'employee_id' AS column_name,
  COUNT(*) AS eligible_rows,
  COUNT(DISTINCT "employee_id") AS eligible_employees,
  SUM(CASE WHEN NULLIF(TRIM(CAST("employee_id" AS VARCHAR)), '') IS NOT NULL THEN 1 ELSE 0 END) AS populated_rows,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(CAST("employee_id" AS VARCHAR)), '') IS NOT NULL THEN "employee_id" END) AS populated_employees,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(CAST("employee_id" AS VARCHAR)), '') IS NOT NULL THEN CAST("employee_id" AS VARCHAR(512)) END) AS distinct_values,
  MIN(CASE WHEN NULLIF(TRIM(CAST("employee_id" AS VARCHAR)), '') IS NOT NULL THEN CAST("fis_mo_end_dt" AS DATE) END) AS first_populated_date,
  MAX(CASE WHEN NULLIF(TRIM(CAST("employee_id" AS VARCHAR)), '') IS NOT NULL THEN CAST("fis_mo_end_dt" AS DATE) END) AS latest_populated_date
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" IS NOT NULL
UNION ALL
SELECT
  'is_termed' AS column_name,
  COUNT(*) AS eligible_rows,
  COUNT(DISTINCT "employee_id") AS eligible_employees,
  SUM(CASE WHEN NULLIF(TRIM(CAST("is_termed" AS VARCHAR)), '') IS NOT NULL THEN 1 ELSE 0 END) AS populated_rows,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(CAST("is_termed" AS VARCHAR)), '') IS NOT NULL THEN "employee_id" END) AS populated_employees,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(CAST("is_termed" AS VARCHAR)), '') IS NOT NULL THEN CAST("is_termed" AS VARCHAR(512)) END) AS distinct_values,
  MIN(CASE WHEN NULLIF(TRIM(CAST("is_termed" AS VARCHAR)), '') IS NOT NULL THEN CAST("fis_mo_end_dt" AS DATE) END) AS first_populated_date,
  MAX(CASE WHEN NULLIF(TRIM(CAST("is_termed" AS VARCHAR)), '') IS NOT NULL THEN CAST("fis_mo_end_dt" AS DATE) END) AS latest_populated_date
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" IS NOT NULL
UNION ALL
SELECT
  'term_date' AS column_name,
  COUNT(*) AS eligible_rows,
  COUNT(DISTINCT "employee_id") AS eligible_employees,
  SUM(CASE WHEN NULLIF(TRIM(CAST("term_date" AS VARCHAR)), '') IS NOT NULL THEN 1 ELSE 0 END) AS populated_rows,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(CAST("term_date" AS VARCHAR)), '') IS NOT NULL THEN "employee_id" END) AS populated_employees,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(CAST("term_date" AS VARCHAR)), '') IS NOT NULL THEN CAST("term_date" AS VARCHAR(512)) END) AS distinct_values,
  MIN(CASE WHEN NULLIF(TRIM(CAST("term_date" AS VARCHAR)), '') IS NOT NULL THEN CAST("fis_mo_end_dt" AS DATE) END) AS first_populated_date,
  MAX(CASE WHEN NULLIF(TRIM(CAST("term_date" AS VARCHAR)), '') IS NOT NULL THEN CAST("fis_mo_end_dt" AS DATE) END) AS latest_populated_date
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" IS NOT NULL
UNION ALL
SELECT
  'term_type' AS column_name,
  COUNT(*) AS eligible_rows,
  COUNT(DISTINCT "employee_id") AS eligible_employees,
  SUM(CASE WHEN NULLIF(TRIM(CAST("term_type" AS VARCHAR)), '') IS NOT NULL THEN 1 ELSE 0 END) AS populated_rows,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(CAST("term_type" AS VARCHAR)), '') IS NOT NULL THEN "employee_id" END) AS populated_employees,
  COUNT(DISTINCT CASE WHEN NULLIF(TRIM(CAST("term_type" AS VARCHAR)), '') IS NOT NULL THEN CAST("term_type" AS VARCHAR(512)) END) AS distinct_values,
  MIN(CASE WHEN NULLIF(TRIM(CAST("term_type" AS VARCHAR)), '') IS NOT NULL THEN CAST("fis_mo_end_dt" AS DATE) END) AS first_populated_date,
  MAX(CASE WHEN NULLIF(TRIM(CAST("term_type" AS VARCHAR)), '') IS NOT NULL THEN CAST("fis_mo_end_dt" AS DATE) END) AS latest_populated_date
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" IS NOT NULL
