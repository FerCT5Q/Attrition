WITH snapshot_choice AS (
  SELECT MAX(fis_mo_end_dt) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt <= DATE '2026-08-17'
),
active_nodes AS (
  SELECT
    details.employee_id,
    CAST(details.manager_employee_id AS BIGINT) AS manager_employee_id,
    details.worker_supervisory_organization_level_from_top AS stored_level,
    UPPER(TRIM(CAST(details.job_title AS VARCHAR(512)))) AS normalized_job_title,
    UPPER(TRIM(CAST(details.management_level AS VARCHAR(512)))) AS normalized_management_level
  FROM hrda.post_hire_monthly_worker_dtls AS details
  CROSS JOIN snapshot_choice
  WHERE details.fis_mo_end_dt = snapshot_choice.snapshot_date
    AND details.active_status = 1
    AND details.employee_id IS NOT NULL
),
root_nodes AS (
  SELECT
    employee_id,
    stored_level,
    normalized_job_title,
    normalized_management_level
  FROM active_nodes
  WHERE manager_employee_id IS NULL
)
SELECT
  snapshot_choice.snapshot_date,
  COUNT(*) AS root_count,
  SUM(CASE
    WHEN normalized_job_title LIKE '%CEO%'
      OR normalized_job_title LIKE '%CHIEF EXECUTIVE OFFICER%'
    THEN 1 ELSE 0 END) AS roots_with_ceo_job_title,
  SUM(CASE
    WHEN normalized_management_level LIKE '%CEO%'
      OR normalized_management_level LIKE '%CHIEF EXECUTIVE OFFICER%'
    THEN 1 ELSE 0 END) AS roots_with_ceo_management_level,
  SUM(CASE WHEN normalized_job_title IS NOT NULL THEN 1 ELSE 0 END)
    AS roots_with_populated_job_title,
  MIN(stored_level) AS minimum_root_stored_level,
  MAX(stored_level) AS maximum_root_stored_level
FROM root_nodes
CROSS JOIN snapshot_choice
GROUP BY snapshot_choice.snapshot_date;
