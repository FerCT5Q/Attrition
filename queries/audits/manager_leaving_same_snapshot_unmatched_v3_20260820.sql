WITH target_snapshots AS (
  SELECT DISTINCT
    employee_id,
    fis_mo_end_dt AS snapshot_date,
    CAST(manager_employee_id AS BIGINT) AS manager_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
    AND manager_employee_id IS NOT NULL
), manager_snapshots AS (
  SELECT DISTINCT employee_id AS manager_id, fis_mo_end_dt AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE employee_id IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
), manager_bounds AS (
  SELECT manager_id, MIN(snapshot_date) AS first_snapshot_date, MAX(snapshot_date) AS last_snapshot_date
  FROM manager_snapshots
  GROUP BY 1
), unmatched AS (
  SELECT s.employee_id, s.snapshot_date, s.manager_id
  FROM target_snapshots s
  LEFT JOIN manager_snapshots m
    ON m.manager_id = s.manager_id
   AND m.snapshot_date = s.snapshot_date
  WHERE m.manager_id IS NULL
), classified AS (
  SELECT
    u.employee_id,
    u.snapshot_date,
    u.manager_id,
    CASE
      WHEN b.manager_id IS NULL THEN 'never_observed'
      WHEN u.snapshot_date < b.first_snapshot_date THEN 'before_manager_history'
      WHEN u.snapshot_date > b.last_snapshot_date THEN 'after_manager_history'
      ELSE 'gap_inside_manager_history'
    END AS mismatch_class
  FROM unmatched u
  LEFT JOIN manager_bounds b
    ON b.manager_id = u.manager_id
)
SELECT
  'Manager leaving' AS variable_name,
  COUNT(*) AS same_snapshot_manager_unmatched_count,
  SUM(CASE WHEN mismatch_class = 'never_observed' THEN 1 ELSE 0 END) AS never_observed_count,
  SUM(CASE WHEN mismatch_class = 'before_manager_history' THEN 1 ELSE 0 END) AS before_manager_history_count,
  SUM(CASE WHEN mismatch_class = 'after_manager_history' THEN 1 ELSE 0 END) AS after_manager_history_count,
  SUM(CASE WHEN mismatch_class = 'gap_inside_manager_history' THEN 1 ELSE 0 END) AS gap_inside_manager_history_count,
  COUNT(DISTINCT snapshot_date) AS affected_snapshot_month_count
FROM classified;

