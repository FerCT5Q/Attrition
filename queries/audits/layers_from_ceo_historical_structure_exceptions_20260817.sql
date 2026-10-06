WITH raw_nodes AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    CAST(manager_employee_id AS BIGINT) AS manager_employee_id,
    UPPER(TRIM(CAST(job_title AS VARCHAR(512)))) AS normalized_job_title,
    worker_type,
    employee_type
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt >= DATE '2023-03-26'
    AND fis_mo_end_dt <= DATE '2026-08-17'
    AND active_status = 1
    AND employee_id IS NOT NULL
),
nodes AS (
  SELECT
    snapshot_date,
    employee_id,
    MIN(manager_employee_id) AS manager_employee_id,
    MAX(CASE
      WHEN normalized_job_title LIKE '%CEO%'
        OR normalized_job_title LIKE '%CHIEF EXECUTIVE OFFICER%'
      THEN 1 ELSE 0 END) AS ceo_title_flag,
    MAX(CASE
      WHEN worker_type = 'Employee'
       AND employee_type = 'Regular'
      THEN 1 ELSE 0 END) AS eligible_flag
  FROM raw_nodes
  GROUP BY snapshot_date, employee_id
),
node_status AS (
  SELECT
    nodes.snapshot_date,
    nodes.employee_id,
    nodes.manager_employee_id,
    nodes.ceo_title_flag,
    nodes.eligible_flag,
    CASE WHEN manager.employee_id IS NOT NULL THEN 1 ELSE 0 END AS manager_found_flag
  FROM nodes
  LEFT JOIN nodes AS manager
    ON manager.snapshot_date = nodes.snapshot_date
   AND manager.employee_id = nodes.manager_employee_id
),
snapshot_structure AS (
  SELECT
    snapshot_date,
    COUNT(*) AS active_node_count,
    SUM(eligible_flag) AS eligible_count,
    SUM(CASE WHEN manager_employee_id IS NULL THEN 1 ELSE 0 END) AS root_count,
    SUM(CASE
      WHEN manager_employee_id IS NULL AND ceo_title_flag = 1
      THEN 1 ELSE 0 END) AS roots_with_ceo_title,
    SUM(CASE
      WHEN manager_employee_id IS NOT NULL AND manager_found_flag = 0
      THEN 1 ELSE 0 END) AS nodes_with_manager_not_found,
    SUM(CASE
      WHEN eligible_flag = 1
       AND manager_employee_id IS NOT NULL
       AND manager_found_flag = 0
      THEN 1 ELSE 0 END) AS eligible_nodes_with_direct_manager_not_found
  FROM node_status
  GROUP BY snapshot_date
)
SELECT
  snapshot_date,
  active_node_count,
  eligible_count,
  root_count,
  roots_with_ceo_title,
  nodes_with_manager_not_found,
  eligible_nodes_with_direct_manager_not_found
FROM snapshot_structure
WHERE root_count <> 1
   OR roots_with_ceo_title <> 1
   OR nodes_with_manager_not_found > 0
ORDER BY snapshot_date;
