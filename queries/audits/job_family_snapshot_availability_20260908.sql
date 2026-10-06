-- Claim: the Job Family comparison can only use employee snapshots available
-- on or before the review cutoff (2026-09-08).
-- Semantic type: direct_field availability check; employee-month snapshot grain.
-- Deliverable mode: internal_analysis. Aggregate-only output.
-- Population: active regular employees
--   (worker_type = 'Employee', employee_type = 'Regular', active_status = 1).
-- Acceptance rule:
--   1) the latest returned snapshot_date must be on or before 2026-09-08; and
--   2) 2026-09-27 must not appear, because it is after the review cutoff.
-- Any row after the cutoff is a source-timestamp anomaly and cannot be used
-- in the deck without source-owner clarification.
SELECT
  CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
  COUNT(DISTINCT employee_id) AS active_regular_employee_count
FROM hrda.post_hire_monthly_worker_dtls
WHERE worker_type = 'Employee'
  AND employee_type = 'Regular'
  AND active_status = 1
  AND CAST(fis_mo_end_dt AS DATE) >= DATE '2026-07-01'
GROUP BY 1
ORDER BY 1 DESC;
