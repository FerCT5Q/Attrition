/*
  Preflight shared by the V7 August-cutoff refresh.

  Purpose: verify the requested fiscal-month-end snapshots before calculating
  the Job family display, Rehire trailing-12-month cohorts, Commute display,
  and manager office-site proximity cohorts.

  Deliverable mode: internal_analysis. Aggregate-only; no employee fields are
  returned. A requested date passes when each active Regular Employee has one
  row at that monthly snapshot.
*/
SELECT
  CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
  COUNT(*) AS active_regular_source_rows,
  COUNT(DISTINCT employee_id) AS active_regular_employees,
  COUNT(*) - COUNT(DISTINCT employee_id) AS duplicate_employee_rows
FROM hrda.post_hire_monthly_worker_dtls
WHERE CAST(fis_mo_end_dt AS DATE) IN (
    DATE '2023-08-27',
    DATE '2024-08-25',
    DATE '2025-08-24',
    DATE '2026-08-23'
  )
  AND worker_type = 'Employee'
  AND employee_type = 'Regular'
  AND active_status = 1
GROUP BY 1
ORDER BY 1;
