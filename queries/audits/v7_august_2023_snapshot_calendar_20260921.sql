/* Aggregate calendar check for the August 2023 fiscal snapshot. */
SELECT
  CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
  COUNT(DISTINCT employee_id) AS active_regular_employees
FROM hrda.post_hire_monthly_worker_dtls
WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2023-08-01' AND DATE '2023-09-15'
  AND worker_type = 'Employee'
  AND employee_type = 'Regular'
  AND active_status = 1
GROUP BY 1
ORDER BY 1;
