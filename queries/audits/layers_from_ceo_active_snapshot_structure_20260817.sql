WITH snapshot_choice AS (
  SELECT MAX(fis_mo_end_dt) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt <= DATE '2026-08-17'
),
raw_nodes AS (
  SELECT
    details.employee_id,
    CAST(details.manager_employee_id AS BIGINT) AS manager_employee_id,
    details.worker_supervisory_organization_level_from_top AS stored_level,
    UPPER(TRIM(CAST(details.job_title AS VARCHAR(512)))) AS normalized_job_title,
    UPPER(TRIM(CAST(details.management_level AS VARCHAR(512)))) AS normalized_management_level,
    details.worker_type,
    details.employee_type
  FROM hrda.post_hire_monthly_worker_dtls AS details
  CROSS JOIN snapshot_choice
  WHERE details.fis_mo_end_dt = snapshot_choice.snapshot_date
    AND details.active_status = 1
    AND details.employee_id IS NOT NULL
),
node_rollup AS (
  SELECT
    employee_id,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT manager_employee_id) AS distinct_nonnull_managers,
    MIN(manager_employee_id) AS manager_employee_id,
    COUNT(DISTINCT stored_level) AS distinct_stored_levels,
    MIN(stored_level) AS stored_level,
    MAX(CASE
      WHEN normalized_job_title = 'CEO'
        OR normalized_job_title LIKE '%CHIEF EXECUTIVE OFFICER%'
        OR normalized_management_level = 'CEO'
        OR normalized_management_level LIKE '%CHIEF EXECUTIVE OFFICER%'
      THEN 1 ELSE 0 END) AS ceo_title_flag,
    MAX(CASE
      WHEN worker_type = 'Employee'
       AND employee_type = 'Regular'
      THEN 1 ELSE 0 END) AS eligible_flag
  FROM raw_nodes
  GROUP BY employee_id
),
node_status AS (
  SELECT
    nodes.employee_id,
    nodes.source_rows,
    nodes.distinct_nonnull_managers,
    nodes.manager_employee_id,
    nodes.distinct_stored_levels,
    nodes.stored_level,
    nodes.ceo_title_flag,
    nodes.eligible_flag,
    CASE WHEN manager.employee_id IS NOT NULL THEN 1 ELSE 0 END AS manager_found_flag
  FROM node_rollup AS nodes
  LEFT JOIN node_rollup AS manager
    ON manager.employee_id = nodes.manager_employee_id
)
SELECT
  snapshot_choice.snapshot_date,
  COUNT(*) AS node_count,
  SUM(eligible_flag) AS eligible_count,
  SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END) AS nodes_with_duplicate_source_rows,
  SUM(CASE WHEN distinct_nonnull_managers > 1 THEN 1 ELSE 0 END)
    AS nodes_with_multiple_managers,
  SUM(CASE WHEN distinct_stored_levels > 1 THEN 1 ELSE 0 END)
    AS nodes_with_multiple_stored_levels,
  SUM(CASE WHEN manager_employee_id IS NULL THEN 1 ELSE 0 END) AS null_manager_nodes,
  SUM(CASE WHEN manager_employee_id = employee_id THEN 1 ELSE 0 END) AS self_manager_nodes,
  SUM(CASE
    WHEN manager_employee_id IS NOT NULL
     AND manager_employee_id <> employee_id
     AND manager_found_flag = 0
    THEN 1 ELSE 0 END) AS manager_not_found_nodes,
  SUM(CASE
    WHEN manager_employee_id IS NULL
      OR manager_employee_id = employee_id
      OR manager_found_flag = 0
    THEN 1 ELSE 0 END) AS root_candidate_nodes,
  SUM(CASE
    WHEN (manager_employee_id IS NULL
       OR manager_employee_id = employee_id
       OR manager_found_flag = 0)
     AND ceo_title_flag = 1
    THEN 1 ELSE 0 END) AS root_candidates_with_ceo_title,
  SUM(CASE WHEN eligible_flag = 1 AND stored_level IS NULL THEN 1 ELSE 0 END)
    AS eligible_missing_stored_level
FROM node_status
CROSS JOIN snapshot_choice
GROUP BY snapshot_choice.snapshot_date;
