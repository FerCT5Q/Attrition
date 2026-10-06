/*
  QVoice heartbeat: workforce denominator for the Jan-2026 wave.

  Aggregate-only profile. The snapshot is the last closed HRDA monthly
  snapshot before the Jan-2026 survey wave. No employee rows or identifiers
  are returned.
*/
SELECT
    DATE '2025-12-28' AS snapshot_date,
    COUNT(*) AS snapshot_rows,
    COUNT(DISTINCT employee_id) AS eligible_employees,
    SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END) AS null_employee_rows
FROM hrda.post_hire_monthly_worker_dtls
WHERE fis_mo_end_dt = DATE '2025-12-28'
  AND worker_type = 'Employee'
  AND employee_type = 'Regular'
  AND active_status = 1;
