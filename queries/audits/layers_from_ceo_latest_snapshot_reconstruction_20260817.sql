WITH RECURSIVE
snapshot_choice AS (
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
    details.worker_type,
    details.employee_type
  FROM hrda.post_hire_monthly_worker_dtls AS details
  CROSS JOIN snapshot_choice
  WHERE details.fis_mo_end_dt = snapshot_choice.snapshot_date
    AND details.active_status = 1
    AND details.employee_id IS NOT NULL
),
nodes AS (
  SELECT
    employee_id,
    MIN(manager_employee_id) AS manager_employee_id,
    MIN(stored_level) AS stored_level,
    MAX(CASE
      WHEN normalized_job_title LIKE '%CEO%'
        OR normalized_job_title LIKE '%CHIEF EXECUTIVE OFFICER%'
      THEN 1 ELSE 0 END) AS ceo_title_flag,
    MAX(CASE
      WHEN worker_type = 'Employee'
       AND employee_type = 'Regular'
      THEN 1 ELSE 0 END) AS eligible_flag
  FROM raw_nodes
  GROUP BY employee_id
  HAVING COUNT(DISTINCT manager_employee_id) <= 1
     AND COUNT(DISTINCT stored_level) <= 1
),
hierarchy_walk (
  origin_employee_id,
  origin_stored_level,
  current_employee_id,
  next_manager_employee_id,
  current_ceo_title_flag,
  reconstructed_depth,
  visited_path,
  cycle_flag
) AS (
  SELECT
    nodes.employee_id AS origin_employee_id,
    nodes.stored_level AS origin_stored_level,
    nodes.employee_id AS current_employee_id,
    nodes.manager_employee_id AS next_manager_employee_id,
    nodes.ceo_title_flag AS current_ceo_title_flag,
    0 AS reconstructed_depth,
    CAST('|' || CAST(nodes.employee_id AS VARCHAR(32)) || '|' AS VARCHAR(4096))
      AS visited_path,
    0 AS cycle_flag
  FROM nodes
  WHERE nodes.eligible_flag = 1

  UNION ALL

  SELECT
    hierarchy_walk.origin_employee_id,
    hierarchy_walk.origin_stored_level,
    manager.employee_id AS current_employee_id,
    manager.manager_employee_id AS next_manager_employee_id,
    manager.ceo_title_flag AS current_ceo_title_flag,
    hierarchy_walk.reconstructed_depth + 1 AS reconstructed_depth,
    CAST(
      hierarchy_walk.visited_path
      || CAST(manager.employee_id AS VARCHAR(32))
      || '|'
      AS VARCHAR(4096)
    ) AS visited_path,
    CASE
      WHEN POSITION(
        '|' || CAST(manager.employee_id AS VARCHAR(32)) || '|'
        IN hierarchy_walk.visited_path
      ) > 0
      THEN 1 ELSE 0
    END AS cycle_flag
  FROM hierarchy_walk
  JOIN nodes AS manager
    ON manager.employee_id = hierarchy_walk.next_manager_employee_id
  WHERE hierarchy_walk.next_manager_employee_id IS NOT NULL
    AND hierarchy_walk.cycle_flag = 0
    AND hierarchy_walk.reconstructed_depth < 25
),
terminal_ranked AS (
  SELECT
    hierarchy_walk.origin_employee_id,
    hierarchy_walk.origin_stored_level,
    hierarchy_walk.current_employee_id,
    hierarchy_walk.next_manager_employee_id,
    hierarchy_walk.current_ceo_title_flag,
    hierarchy_walk.reconstructed_depth,
    hierarchy_walk.cycle_flag,
    ROW_NUMBER() OVER (
      PARTITION BY origin_employee_id
      ORDER BY reconstructed_depth DESC
    ) AS terminal_rank
  FROM hierarchy_walk
),
terminal AS (
  SELECT
    origin_employee_id,
    origin_stored_level,
    current_employee_id AS terminal_employee_id,
    next_manager_employee_id,
    current_ceo_title_flag,
    reconstructed_depth,
    cycle_flag,
    CASE
      WHEN cycle_flag = 0 AND next_manager_employee_id IS NULL THEN 1 ELSE 0
    END AS resolved_flag,
    CASE
      WHEN cycle_flag = 0 AND next_manager_employee_id IS NOT NULL THEN 1 ELSE 0
    END AS unresolved_flag
  FROM terminal_ranked
  WHERE terminal_rank = 1
),
root_distribution AS (
  SELECT
    terminal_employee_id,
    MAX(current_ceo_title_flag) AS root_ceo_title_flag,
    COUNT(*) AS resolved_employees
  FROM terminal
  WHERE resolved_flag = 1
  GROUP BY terminal_employee_id
),
root_summary AS (
  SELECT
    COUNT(*) AS root_count,
    SUM(CASE WHEN root_ceo_title_flag = 1 THEN 1 ELSE 0 END) AS roots_with_ceo_title,
    MAX(resolved_employees) AS largest_root_employee_count
  FROM root_distribution
),
terminal_summary AS (
  SELECT
    COUNT(*) AS eligible_count,
    SUM(resolved_flag) AS reconstructed_count,
    SUM(unresolved_flag) AS unresolved_count,
    SUM(cycle_flag) AS cycle_count,
    MAX(reconstructed_depth) AS maximum_reconstructed_depth,
    SUM(CASE
      WHEN resolved_flag = 1 AND origin_stored_level IS NOT NULL
      THEN 1 ELSE 0 END) AS comparable_count,
    SUM(CASE
      WHEN resolved_flag = 1
       AND origin_stored_level = reconstructed_depth + 1
      THEN 1 ELSE 0 END) AS matched_depth_plus_one_count,
    SUM(CASE
      WHEN resolved_flag = 1
       AND origin_stored_level IS NOT NULL
       AND origin_stored_level <> reconstructed_depth + 1
      THEN 1 ELSE 0 END) AS depth_mismatch_count,
    SUM(CASE
      WHEN resolved_flag = 1
       AND origin_stored_level = reconstructed_depth
      THEN 1 ELSE 0 END) AS matched_depth_zero_based_count
  FROM terminal
),
edge_summary AS (
  SELECT
    COUNT(*) AS comparable_employee_manager_edges,
    SUM(CASE WHEN child.stored_level = manager.stored_level + 1 THEN 1 ELSE 0 END)
      AS employee_manager_edges_plus_one,
    SUM(CASE WHEN child.stored_level <> manager.stored_level + 1 THEN 1 ELSE 0 END)
      AS employee_manager_edge_mismatches
  FROM nodes AS child
  JOIN nodes AS manager
    ON manager.employee_id = child.manager_employee_id
  WHERE child.eligible_flag = 1
    AND child.stored_level IS NOT NULL
    AND manager.stored_level IS NOT NULL
)
SELECT
  snapshot_choice.snapshot_date,
  terminal_summary.eligible_count,
  terminal_summary.reconstructed_count,
  terminal_summary.unresolved_count,
  terminal_summary.cycle_count,
  root_summary.root_count,
  root_summary.roots_with_ceo_title,
  CASE
    WHEN root_summary.root_count = 1
     AND root_summary.roots_with_ceo_title = 1
    THEN 1 ELSE 0
  END AS root_semantics_pass,
  ROUND(
    100.0 * root_summary.largest_root_employee_count
    / NULLIF(terminal_summary.reconstructed_count, 0),
    4
  ) AS convergence_rate_percent,
  terminal_summary.maximum_reconstructed_depth,
  terminal_summary.comparable_count,
  terminal_summary.matched_depth_plus_one_count,
  terminal_summary.depth_mismatch_count,
  ROUND(
    100.0 * terminal_summary.matched_depth_plus_one_count
    / NULLIF(terminal_summary.comparable_count, 0),
    4
  ) AS match_rate_percent,
  terminal_summary.matched_depth_zero_based_count,
  edge_summary.comparable_employee_manager_edges,
  edge_summary.employee_manager_edges_plus_one,
  edge_summary.employee_manager_edge_mismatches,
  ROUND(
    100.0 * edge_summary.employee_manager_edges_plus_one
    / NULLIF(edge_summary.comparable_employee_manager_edges, 0),
    4
  ) AS employee_manager_plus_one_rate_percent
FROM terminal_summary
CROSS JOIN root_summary
CROSS JOIN edge_summary
CROSS JOIN snapshot_choice;
