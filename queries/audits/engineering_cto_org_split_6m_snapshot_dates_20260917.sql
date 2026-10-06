/* Latest 24 snapshot dates with a complete six-month follow-up; aggregate metadata only. */
WITH source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
)
SELECT CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
       COUNT(DISTINCT CAST(w.employee_id AS VARCHAR(64))) AS employee_count
FROM hrda.post_hire_monthly_worker_dtls AS w
CROSS JOIN source_bounds AS b
WHERE w.fis_mo_end_dt IS NOT NULL
  AND CAST(w.fis_mo_end_dt AS DATE) <= DATEADD(month, -6, b.latest_snapshot_date)
GROUP BY 1
ORDER BY snapshot_date DESC
LIMIT 24;
