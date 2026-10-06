-- Claim: the primary manager population is reconstructed from active regular
-- direct-report relationships at each monthly snapshot. Stored report counts
-- are supporting controls and are never used as an assumed manager flag.
-- Deliverable mode: presentation; aggregate-only output.
-- Acceptance rule: each snapshot has at least 30 reconstructed managers and
-- zero duplicate employee-snapshot rows. Count-field differences are reported.

WITH parameters AS (
  SELECT DATE '2026-09-27' AS cutoff_date
),
raw_active_rows AS (
  SELECT
    CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
    w.employee_id,
    w.manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN parameters AS p
  WHERE CAST(w.fis_mo_end_dt AS DATE) BETWEEN DATEADD(month, -11, p.cutoff_date) AND p.cutoff_date
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
),
duplicate_employee_snapshots AS (
  SELECT snapshot_date, employee_id, COUNT(*) AS row_count
  FROM raw_active_rows
  GROUP BY 1, 2
),
active_workers AS (
  SELECT DISTINCT snapshot_date, employee_id, manager_employee_id
  FROM raw_active_rows
),
reconstructed_teams AS (
  SELECT
    snapshot_date,
    manager_employee_id AS manager_id,
    COUNT(DISTINCT employee_id) AS reconstructed_direct_reports
  FROM active_workers
  WHERE manager_employee_id IS NOT NULL
  GROUP BY 1, 2
),
manager_directory_rows AS (
  SELECT
    CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
    w.employee_id AS manager_id,
    w.reg_non_intern_dir_reports,
    w.all_dir_reports,
    COUNT(*) OVER (
      PARTITION BY CAST(w.fis_mo_end_dt AS DATE), w.employee_id
    ) AS manager_directory_row_count
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN parameters AS p
  WHERE CAST(w.fis_mo_end_dt AS DATE) BETWEEN DATEADD(month, -11, p.cutoff_date) AND p.cutoff_date
),
manager_directory_ranked AS (
  SELECT
    snapshot_date,
    manager_id,
    reg_non_intern_dir_reports,
    all_dir_reports,
    manager_directory_row_count,
    ROW_NUMBER() OVER (
      PARTITION BY snapshot_date, manager_id
      ORDER BY manager_directory_row_count DESC, manager_id
    ) AS directory_rank
  FROM manager_directory_rows
),
manager_directory AS (
  SELECT snapshot_date, manager_id, reg_non_intern_dir_reports, all_dir_reports,
    manager_directory_row_count
  FROM manager_directory_ranked
  WHERE directory_rank = 1
),
comparison AS (
  SELECT
    t.snapshot_date,
    t.manager_id,
    t.reconstructed_direct_reports,
    d.manager_id AS directory_manager_id,
    d.manager_directory_row_count,
    d.reg_non_intern_dir_reports,
    d.all_dir_reports
  FROM reconstructed_teams AS t
  LEFT JOIN manager_directory AS d
    ON d.snapshot_date = t.snapshot_date
   AND d.manager_id = t.manager_id
)
SELECT
  snapshot_date,
  COUNT(*) AS reconstructed_manager_count,
  SUM(reconstructed_direct_reports) AS reconstructed_direct_report_count,
  SUM(CASE WHEN directory_manager_id IS NOT NULL THEN 1 ELSE 0 END) AS manager_directory_matched_count,
  SUM(CASE WHEN directory_manager_id IS NULL THEN 1 ELSE 0 END) AS manager_directory_unmatched_count,
  SUM(CASE WHEN manager_directory_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_manager_directory_keys,
  SUM(CASE WHEN COALESCE(reg_non_intern_dir_reports, 0) > 0 THEN 1 ELSE 0 END) AS reg_non_intern_positive_count,
  SUM(CASE WHEN COALESCE(all_dir_reports, 0) > 0 THEN 1 ELSE 0 END) AS all_dir_positive_count,
  SUM(CASE WHEN reg_non_intern_dir_reports = reconstructed_direct_reports THEN 1 ELSE 0 END) AS reg_non_intern_exact_count,
  SUM(CASE WHEN all_dir_reports = reconstructed_direct_reports THEN 1 ELSE 0 END) AS all_dir_exact_count,
  SUM(CASE WHEN reg_non_intern_dir_reports IS NULL THEN 1 ELSE 0 END) AS reg_non_intern_null_count,
  SUM(CASE WHEN all_dir_reports IS NULL THEN 1 ELSE 0 END) AS all_dir_null_count,
  (SELECT COALESCE(SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END), 0)
   FROM duplicate_employee_snapshots AS d
   WHERE d.snapshot_date = c.snapshot_date) AS duplicate_employee_snapshot_rows
FROM comparison AS c
GROUP BY 1
ORDER BY snapshot_date;
