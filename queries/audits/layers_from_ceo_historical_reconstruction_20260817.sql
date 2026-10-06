WITH RECURSIVE
raw_nodes AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    CAST(manager_employee_id AS BIGINT) AS manager_employee_id,
    worker_supervisory_organization_level_from_top AS stored_level,
    UPPER(TRIM(CAST(job_title AS VARCHAR(512)))) AS normalized_job_title,
    worker_type,
    employee_type
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt >= DATE '2023-03-26'
    AND fis_mo_end_dt <= DATE '2026-08-17'
    AND active_status = 1
    AND employee_id IS NOT NULL
),
node_rollup AS (
  SELECT
    snapshot_date,
    employee_id,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT COALESCE(manager_employee_id, -1)) AS manager_variants,
    MIN(manager_employee_id) AS manager_employee_id,
    COUNT(DISTINCT COALESCE(stored_level, -9999)) AS stored_level_variants,
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
  GROUP BY snapshot_date, employee_id
),
nodes AS (
  SELECT
    snapshot_date,
    employee_id,
    manager_employee_id,
    stored_level,
    ceo_title_flag,
    eligible_flag
  FROM node_rollup
  WHERE manager_variants = 1
    AND stored_level_variants = 1
),
eligible_by_snapshot AS (
  SELECT
    snapshot_date,
    SUM(eligible_flag) AS eligible_count,
    SUM(CASE
      WHEN eligible_flag = 1
       AND (manager_variants <> 1 OR stored_level_variants <> 1)
      THEN 1 ELSE 0 END) AS ambiguous_eligible_count,
    SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END) AS duplicate_node_count,
    SUM(CASE WHEN manager_variants > 1 THEN 1 ELSE 0 END) AS multiple_manager_nodes,
    SUM(CASE WHEN stored_level_variants > 1 THEN 1 ELSE 0 END)
      AS multiple_stored_level_nodes
  FROM node_rollup
  GROUP BY snapshot_date
),
hierarchy_walk (
  snapshot_date,
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
    nodes.snapshot_date,
    nodes.employee_id AS origin_employee_id,
    nodes.stored_level AS origin_stored_level,
    nodes.employee_id AS current_employee_id,
    nodes.manager_employee_id AS next_manager_employee_id,
    nodes.ceo_title_flag AS current_ceo_title_flag,
    0 AS reconstructed_depth,
    CAST('|' || CAST(nodes.employee_id AS VARCHAR(32)) || '|' AS VARCHAR(1024))
      AS visited_path,
    0 AS cycle_flag
  FROM nodes
  WHERE nodes.eligible_flag = 1

  UNION ALL

  SELECT
    hierarchy_walk.snapshot_date,
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
      AS VARCHAR(1024)
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
    ON manager.snapshot_date = hierarchy_walk.snapshot_date
   AND manager.employee_id = hierarchy_walk.next_manager_employee_id
  WHERE hierarchy_walk.next_manager_employee_id IS NOT NULL
    AND hierarchy_walk.cycle_flag = 0
    AND hierarchy_walk.reconstructed_depth < 25
),
terminal_ranked AS (
  SELECT
    hierarchy_walk.snapshot_date,
    hierarchy_walk.origin_employee_id,
    hierarchy_walk.origin_stored_level,
    hierarchy_walk.current_employee_id,
    hierarchy_walk.next_manager_employee_id,
    hierarchy_walk.current_ceo_title_flag,
    hierarchy_walk.reconstructed_depth,
    hierarchy_walk.cycle_flag,
    ROW_NUMBER() OVER (
      PARTITION BY hierarchy_walk.snapshot_date, hierarchy_walk.origin_employee_id
      ORDER BY hierarchy_walk.reconstructed_depth DESC
    ) AS terminal_rank
  FROM hierarchy_walk
),
terminal AS (
  SELECT
    snapshot_date,
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
terminal_by_snapshot AS (
  SELECT
    snapshot_date,
    COUNT(*) AS walked_eligible_count,
    SUM(resolved_flag) AS reconstructed_count,
    SUM(CASE
      WHEN resolved_flag = 1 AND current_ceo_title_flag = 1
      THEN 1 ELSE 0 END) AS reconstructed_to_ceo_count,
    SUM(CASE
      WHEN resolved_flag = 1 AND current_ceo_title_flag = 0
      THEN 1 ELSE 0 END) AS reconstructed_to_non_ceo_root_count,
    SUM(unresolved_flag) AS unresolved_walk_count,
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
      THEN 1 ELSE 0 END) AS depth_mismatch_count
  FROM terminal
  GROUP BY snapshot_date
),
root_distribution AS (
  SELECT
    snapshot_date,
    terminal_employee_id,
    MAX(current_ceo_title_flag) AS root_ceo_title_flag,
    COUNT(*) AS resolved_employees
  FROM terminal
  WHERE resolved_flag = 1
  GROUP BY snapshot_date, terminal_employee_id
),
root_by_snapshot AS (
  SELECT
    snapshot_date,
    COUNT(*) AS root_count,
    SUM(CASE WHEN root_ceo_title_flag = 1 THEN 1 ELSE 0 END) AS roots_with_ceo_title,
    MAX(resolved_employees) AS largest_root_employee_count
  FROM root_distribution
  GROUP BY snapshot_date
),
edge_by_snapshot AS (
  SELECT
    child.snapshot_date,
    COUNT(*) AS comparable_employee_manager_edges,
    SUM(CASE WHEN child.stored_level = manager.stored_level + 1 THEN 1 ELSE 0 END)
      AS employee_manager_edges_plus_one,
    SUM(CASE WHEN child.stored_level <> manager.stored_level + 1 THEN 1 ELSE 0 END)
      AS employee_manager_edge_mismatches
  FROM nodes AS child
  JOIN nodes AS manager
    ON manager.snapshot_date = child.snapshot_date
   AND manager.employee_id = child.manager_employee_id
  WHERE child.eligible_flag = 1
    AND child.stored_level IS NOT NULL
    AND manager.stored_level IS NOT NULL
  GROUP BY child.snapshot_date
),
snapshot_results AS (
  SELECT
    eligible_by_snapshot.snapshot_date,
    eligible_by_snapshot.eligible_count,
    eligible_by_snapshot.ambiguous_eligible_count,
    eligible_by_snapshot.duplicate_node_count,
    eligible_by_snapshot.multiple_manager_nodes,
    eligible_by_snapshot.multiple_stored_level_nodes,
    COALESCE(terminal_by_snapshot.reconstructed_count, 0) AS reconstructed_count,
    COALESCE(terminal_by_snapshot.reconstructed_to_ceo_count, 0)
      AS reconstructed_to_ceo_count,
    COALESCE(terminal_by_snapshot.reconstructed_to_non_ceo_root_count, 0)
      AS reconstructed_to_non_ceo_root_count,
    COALESCE(terminal_by_snapshot.unresolved_walk_count, 0)
      + eligible_by_snapshot.eligible_count
      - COALESCE(terminal_by_snapshot.walked_eligible_count, 0) AS unresolved_count,
    COALESCE(terminal_by_snapshot.cycle_count, 0) AS cycle_count,
    COALESCE(root_by_snapshot.root_count, 0) AS root_count,
    COALESCE(root_by_snapshot.roots_with_ceo_title, 0) AS roots_with_ceo_title,
    CASE
      WHEN root_by_snapshot.root_count = 1
       AND root_by_snapshot.roots_with_ceo_title = 1
      THEN 1 ELSE 0
    END AS root_semantics_pass,
    100.0 * root_by_snapshot.largest_root_employee_count
      / NULLIF(terminal_by_snapshot.reconstructed_count, 0)
      AS convergence_rate_percent,
    terminal_by_snapshot.maximum_reconstructed_depth,
    terminal_by_snapshot.comparable_count,
    terminal_by_snapshot.matched_depth_plus_one_count,
    terminal_by_snapshot.depth_mismatch_count,
    edge_by_snapshot.comparable_employee_manager_edges,
    edge_by_snapshot.employee_manager_edges_plus_one,
    edge_by_snapshot.employee_manager_edge_mismatches
  FROM eligible_by_snapshot
  LEFT JOIN terminal_by_snapshot
    ON terminal_by_snapshot.snapshot_date = eligible_by_snapshot.snapshot_date
  LEFT JOIN root_by_snapshot
    ON root_by_snapshot.snapshot_date = eligible_by_snapshot.snapshot_date
  LEFT JOIN edge_by_snapshot
    ON edge_by_snapshot.snapshot_date = eligible_by_snapshot.snapshot_date
)
SELECT
  MIN(snapshot_date) AS first_snapshot_date,
  MAX(snapshot_date) AS latest_snapshot_date,
  COUNT(*) AS snapshots_checked,
  SUM(eligible_count) AS eligible_count,
  SUM(reconstructed_count) AS reconstructed_count,
  SUM(reconstructed_to_ceo_count) AS reconstructed_to_ceo_count,
  SUM(reconstructed_to_non_ceo_root_count) AS reconstructed_to_non_ceo_root_count,
  SUM(unresolved_count) AS unresolved_count,
  SUM(cycle_count) AS cycle_count,
  SUM(ambiguous_eligible_count) AS ambiguous_eligible_count,
  SUM(duplicate_node_count) AS duplicate_node_count,
  SUM(multiple_manager_nodes) AS multiple_manager_nodes,
  SUM(multiple_stored_level_nodes) AS multiple_stored_level_nodes,
  MIN(root_count) AS minimum_root_count,
  MAX(root_count) AS maximum_root_count,
  SUM(CASE WHEN root_count = 1 THEN 1 ELSE 0 END) AS snapshots_with_one_root,
  SUM(root_semantics_pass) AS snapshots_passing_root_semantics,
  ROUND(MIN(convergence_rate_percent), 4) AS minimum_convergence_rate_percent,
  MAX(maximum_reconstructed_depth) AS maximum_reconstructed_depth,
  SUM(comparable_count) AS comparable_count,
  SUM(matched_depth_plus_one_count) AS matched_depth_plus_one_count,
  SUM(depth_mismatch_count) AS depth_mismatch_count,
  ROUND(
    100.0 * SUM(matched_depth_plus_one_count) / NULLIF(SUM(comparable_count), 0),
    4
  ) AS match_rate_percent,
  SUM(comparable_employee_manager_edges) AS comparable_employee_manager_edges,
  SUM(employee_manager_edges_plus_one) AS employee_manager_edges_plus_one,
  SUM(employee_manager_edge_mismatches) AS employee_manager_edge_mismatches,
  ROUND(
    100.0 * SUM(employee_manager_edges_plus_one)
    / NULLIF(SUM(comparable_employee_manager_edges), 0),
    4
  ) AS employee_manager_plus_one_rate_percent
FROM snapshot_results;
