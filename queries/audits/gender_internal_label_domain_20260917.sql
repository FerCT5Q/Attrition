-- Claim: The V7 internal_analysis Gender slide may show the stored gender
-- labels when each aggregate bucket meets the n >= 30 cohort rule.
-- Semantic type: direct_field.
-- Deliverable mode: internal_analysis.
-- Population: active regular, non-RF360 employees in the six monthly snapshots
-- ending 2026-08-23; one employee-snapshot per employee and month.
-- Grain: stored gender label across aggregate employee-snapshot exposure.
-- Acceptance rule: every emitted stored label must have at least 30 distinct
-- employees, retain a nonempty label, and be observed in all six snapshots.
WITH parameters AS (
  SELECT DATE '2026-08-23' AS cutoff_date
),
employee_snapshots AS (
  SELECT
    CAST(worker.fis_mo_end_dt AS DATE) AS snapshot_date,
    worker.employee_id,
    MAX(NULLIF(TRIM(CAST(worker.gender AS VARCHAR(256))), '')) AS gender
  FROM hrda.post_hire_monthly_worker_dtls AS worker
  CROSS JOIN parameters
  WHERE CAST(worker.fis_mo_end_dt AS DATE) > DATEADD(month, -6, parameters.cutoff_date)
    AND CAST(worker.fis_mo_end_dt AS DATE) <= parameters.cutoff_date
    AND worker.worker_type = 'Employee'
    AND worker.employee_type = 'Regular'
    AND worker.active_status = 1
    AND COALESCE(worker.is_rf360_yes_no, 0) = 0
  GROUP BY 1, 2
)
SELECT
  COALESCE(gender, 'Unknown / other') AS gender,
  COUNT(DISTINCT employee_id) AS employee_count,
  COUNT(*) AS employee_snapshot_count,
  COUNT(DISTINCT snapshot_date) AS snapshot_count,
  MIN(snapshot_date) AS first_snapshot_date,
  MAX(snapshot_date) AS last_snapshot_date
FROM employee_snapshots
GROUP BY 1
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY employee_snapshot_count DESC, gender;
