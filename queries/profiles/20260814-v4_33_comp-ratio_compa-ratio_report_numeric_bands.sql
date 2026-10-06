SELECT
  'compa_ratio' AS column_name,
  CASE WHEN "compa_ratio" < 0.8 THEN '< 0.8' WHEN "compa_ratio" < 0.9 THEN '0.8 to < 0.9' WHEN "compa_ratio" < 1 THEN '0.9 to < 1' WHEN "compa_ratio" < 1.1 THEN '1 to < 1.1' WHEN "compa_ratio" < 1.2 THEN '1.1 to < 1.2' ELSE '>= 1.2' END AS band_label,
  COUNT(DISTINCT "employee_id") AS employee_count,
  COUNT(*) AS row_count
FROM "hrda"."post_hire_monthly_worker_dtls"
WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
  AND "fis_mo_end_dt" = (
    SELECT MAX("fis_mo_end_dt")
    FROM "hrda"."post_hire_monthly_worker_dtls"
    WHERE "worker_type" = 'Employee' AND "employee_type" = 'Regular' AND "active_status" = 1
      AND "fis_mo_end_dt" IS NOT NULL
  )
  AND "compa_ratio" IS NOT NULL
GROUP BY 1, 2
HAVING COUNT(DISTINCT "employee_id") >= 30
ORDER BY MIN("compa_ratio")
