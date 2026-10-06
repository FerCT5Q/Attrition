-- Presentation-safe aggregate audit for slide 32.
--
-- The approved CEO reference is intentionally NOT stored here.  The evidence
-- builder binds %(approved_ceo_employee_id)s from its secure, non-versioned
-- execution environment.  This query returns aggregate diagnostics and raw
-- aggregate depth counts only; employee, manager, and root identifiers stay
-- inside the same-snapshot traversal and are never persisted.
WITH RECURSIVE
snapshot_choice AS (
  SELECT DATE '2026-08-23' AS snapshot_date
),
raw_active_nodes AS (
  SELECT
    CAST(details.employee_id AS BIGINT) AS employee_id,
    CAST(NULLIF(TRIM(CAST(details.manager_employee_id AS VARCHAR(64))), '') AS BIGINT)
      AS manager_employee_id,
    details.worker_supervisory_organization_level_from_top AS stored_level,
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
    COUNT(DISTINCT COALESCE(CAST(manager_employee_id AS VARCHAR(64)), '<NULL>'))
      AS manager_assignment_count,
    MIN(manager_employee_id) AS canonical_manager_employee_id,
    COUNT(DISTINCT stored_level) AS stored_level_value_count,
    MIN(stored_level) AS stored_level,
    MAX(CASE
      WHEN worker_type = 'Employee' AND employee_type = 'Regular' THEN 1
      ELSE 0
    END) AS display_employee_flag
  FROM raw_active_nodes
  GROUP BY employee_id
),
nodes AS (
  SELECT
    employee_id,
    source_rows,
    manager_assignment_count,
    CASE
      WHEN manager_assignment_count = 1 THEN canonical_manager_employee_id
      ELSE NULL
    END AS manager_employee_id,
    stored_level_value_count,
    stored_level,
    display_employee_flag
  FROM node_rollup
),
hierarchy_walk (
  origin_employee_id,
  origin_display_employee_flag,
  origin_stored_level,
  current_employee_id,
  current_manager_employee_id,
  reconstructed_depth,
  visited_path,
  failure_reason
) AS (
  SELECT
    nodes.employee_id AS origin_employee_id,
    nodes.display_employee_flag AS origin_display_employee_flag,
    nodes.stored_level AS origin_stored_level,
    nodes.employee_id AS current_employee_id,
    nodes.manager_employee_id AS current_manager_employee_id,
    0 AS reconstructed_depth,
    CAST('|' || CAST(nodes.employee_id AS VARCHAR(32)) || '|' AS VARCHAR(4096))
      AS visited_path,
    CASE
      WHEN nodes.manager_assignment_count <> 1 THEN 'manager_conflict'
      WHEN nodes.manager_employee_id = nodes.employee_id THEN 'self_manager'
      ELSE NULL
    END AS failure_reason
  FROM nodes

  UNION ALL

  SELECT
    hierarchy_walk.origin_employee_id,
    hierarchy_walk.origin_display_employee_flag,
    hierarchy_walk.origin_stored_level,
    COALESCE(manager_node.employee_id, hierarchy_walk.current_manager_employee_id)
      AS current_employee_id,
    manager_node.manager_employee_id AS current_manager_employee_id,
    CASE
      WHEN hierarchy_walk.reconstructed_depth >= 25
      THEN hierarchy_walk.reconstructed_depth
      ELSE hierarchy_walk.reconstructed_depth + 1
    END AS reconstructed_depth,
    CAST(
      hierarchy_walk.visited_path
      || COALESCE(CAST(manager_node.employee_id AS VARCHAR(32)), '<MISSING>')
      || '|'
      AS VARCHAR(4096)
    ) AS visited_path,
    CASE
      WHEN hierarchy_walk.reconstructed_depth >= 25 THEN 'depth_exceeded'
      WHEN manager_node.employee_id IS NULL THEN 'missing_manager'
      WHEN manager_node.manager_assignment_count <> 1 THEN 'manager_conflict'
      WHEN manager_node.manager_employee_id = manager_node.employee_id THEN 'self_manager'
      WHEN POSITION(
        '|' || CAST(manager_node.employee_id AS VARCHAR(32)) || '|'
        IN hierarchy_walk.visited_path
      ) > 0 THEN 'cycle'
      ELSE NULL
    END AS failure_reason
  FROM hierarchy_walk
  LEFT JOIN nodes AS manager_node
    ON manager_node.employee_id = hierarchy_walk.current_manager_employee_id
  WHERE hierarchy_walk.failure_reason IS NULL
    AND hierarchy_walk.current_manager_employee_id IS NOT NULL
),
terminal_ranked AS (
  SELECT
    hierarchy_walk.origin_employee_id,
    hierarchy_walk.origin_display_employee_flag,
    hierarchy_walk.origin_stored_level,
    hierarchy_walk.current_employee_id,
    hierarchy_walk.current_manager_employee_id,
    hierarchy_walk.reconstructed_depth,
    hierarchy_walk.visited_path,
    hierarchy_walk.failure_reason,
    ROW_NUMBER() OVER (
      PARTITION BY origin_employee_id
      ORDER BY reconstructed_depth DESC
    ) AS terminal_rank
  FROM hierarchy_walk
),
terminal AS (
  SELECT
    origin_employee_id,
    origin_display_employee_flag,
    origin_stored_level,
    current_employee_id AS terminal_root_employee_id,
    current_manager_employee_id,
    reconstructed_depth,
    failure_reason,
    CASE
      WHEN failure_reason IS NULL AND current_manager_employee_id IS NULL THEN 1
      ELSE 0
    END AS reconstructed_flag
  FROM terminal_ranked
  WHERE terminal_rank = 1
),
root_distribution AS (
  SELECT
    terminal_root_employee_id,
    COUNT(*) AS reconstructed_nodes
  FROM terminal
  WHERE reconstructed_flag = 1
  GROUP BY terminal_root_employee_id
),
root_summary AS (
  SELECT
    COUNT(*) AS root_count,
    COALESCE(MAX(reconstructed_nodes), 0) AS largest_root_node_count
  FROM root_distribution
),
universe_summary AS (
  SELECT
    COUNT(*) AS universe_node_count,
    SUM(CASE WHEN reconstructed_flag = 1 THEN 1 ELSE 0 END) AS reconstructed_count,
    SUM(CASE WHEN reconstructed_flag = 0 THEN 1 ELSE 0 END) AS unresolved_chain_count,
    SUM(CASE WHEN failure_reason = 'missing_manager' THEN 1 ELSE 0 END)
      AS missing_manager_chain_count,
    SUM(CASE WHEN failure_reason = 'self_manager' THEN 1 ELSE 0 END)
      AS self_manager_chain_count,
    SUM(CASE WHEN failure_reason = 'cycle' THEN 1 ELSE 0 END) AS cycle_chain_count,
    SUM(CASE WHEN failure_reason = 'depth_exceeded' THEN 1 ELSE 0 END)
      AS depth_exceeded_chain_count,
    SUM(CASE WHEN failure_reason = 'manager_conflict' THEN 1 ELSE 0 END)
      AS manager_conflict_chain_count,
    SUM(CASE
      WHEN reconstructed_flag = 1
       AND terminal_root_employee_id = CAST(%(approved_ceo_employee_id)s AS BIGINT)
      THEN 1 ELSE 0
    END) AS approved_root_resolved_count,
    SUM(CASE
      WHEN reconstructed_flag = 1
       AND terminal_root_employee_id <> CAST(%(approved_ceo_employee_id)s AS BIGINT)
      THEN 1 ELSE 0
    END) AS nonmatching_approved_root_count,
    MAX(reconstructed_depth) AS maximum_observed_depth
  FROM terminal
),
node_quality_summary AS (
  SELECT
    COUNT(*) AS node_count,
    SUM(source_rows) AS active_source_row_count,
    SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END) AS duplicate_source_node_count,
    SUM(CASE WHEN manager_assignment_count <> 1 THEN 1 ELSE 0 END)
      AS manager_conflict_node_count,
    SUM(CASE WHEN manager_employee_id = employee_id THEN 1 ELSE 0 END)
      AS self_manager_node_count,
    SUM(CASE WHEN stored_level_value_count > 1 THEN 1 ELSE 0 END)
      AS stored_level_conflict_node_count
  FROM nodes
),
display_summary AS (
  SELECT
    SUM(CASE WHEN origin_display_employee_flag = 1 THEN 1 ELSE 0 END)
      AS display_eligible_count,
    SUM(CASE
      WHEN origin_display_employee_flag = 1 AND reconstructed_flag = 1
      THEN 1 ELSE 0
    END) AS display_reconstructed_count,
    SUM(CASE
      WHEN origin_display_employee_flag = 1 AND reconstructed_flag = 0
      THEN 1 ELSE 0
    END) AS display_unresolved_chain_count,
    SUM(CASE
      WHEN origin_display_employee_flag = 1
       AND reconstructed_flag = 1
       AND terminal_root_employee_id = CAST(%(approved_ceo_employee_id)s AS BIGINT)
      THEN 1 ELSE 0
    END) AS display_approved_root_match_count,
    SUM(CASE
      WHEN origin_display_employee_flag = 1
       AND reconstructed_flag = 1
       AND origin_stored_level IS NOT NULL
      THEN 1 ELSE 0
    END) AS stored_level_comparable_count,
    SUM(CASE
      WHEN origin_display_employee_flag = 1
       AND reconstructed_flag = 1
       AND origin_stored_level = reconstructed_depth + 1
      THEN 1 ELSE 0
    END) AS stored_level_depth_plus_one_match_count
  FROM terminal
),
depth_distribution AS (
  SELECT
    reconstructed_depth AS depth,
    COUNT(*) AS employee_count
  FROM terminal
  WHERE origin_display_employee_flag = 1
    AND reconstructed_flag = 1
  GROUP BY reconstructed_depth
)
SELECT
  snapshot_choice.snapshot_date,
  'metric' AS row_type,
  metric.metric,
  CAST(NULL AS INTEGER) AS depth,
  metric.metric_value
FROM snapshot_choice
CROSS JOIN universe_summary
CROSS JOIN node_quality_summary
CROSS JOIN root_summary
CROSS JOIN display_summary
CROSS JOIN (
  SELECT 'active_source_row_count' AS metric, CAST(active_source_row_count AS DECIMAL(18, 8)) AS metric_value FROM node_quality_summary
  UNION ALL SELECT 'universe_node_count', CAST(universe_node_count AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'duplicate_source_node_count', CAST(duplicate_source_node_count AS DECIMAL(18, 8)) FROM node_quality_summary
  UNION ALL SELECT 'manager_conflict_node_count', CAST(manager_conflict_node_count AS DECIMAL(18, 8)) FROM node_quality_summary
  UNION ALL SELECT 'self_manager_node_count', CAST(self_manager_node_count AS DECIMAL(18, 8)) FROM node_quality_summary
  UNION ALL SELECT 'stored_level_conflict_node_count', CAST(stored_level_conflict_node_count AS DECIMAL(18, 8)) FROM node_quality_summary
  UNION ALL SELECT 'reconstructed_count', CAST(reconstructed_count AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'unresolved_chain_count', CAST(unresolved_chain_count AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'missing_manager_chain_count', CAST(missing_manager_chain_count AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'self_manager_chain_count', CAST(self_manager_chain_count AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'cycle_chain_count', CAST(cycle_chain_count AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'depth_exceeded_chain_count', CAST(depth_exceeded_chain_count AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'manager_conflict_chain_count', CAST(manager_conflict_chain_count AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'root_count', CAST(root_count AS DECIMAL(18, 8)) FROM root_summary
  UNION ALL SELECT 'approved_root_resolved_count', CAST(approved_root_resolved_count AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'nonmatching_approved_root_count', CAST(nonmatching_approved_root_count AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'maximum_observed_depth', CAST(maximum_observed_depth AS DECIMAL(18, 8)) FROM universe_summary
  UNION ALL SELECT 'convergence_rate_percent', CAST(100.0 * largest_root_node_count / NULLIF(universe_node_count, 0) AS DECIMAL(18, 8)) FROM root_summary CROSS JOIN universe_summary
  UNION ALL SELECT 'root_reference_pass', CAST(CASE WHEN root_count = 1 AND unresolved_chain_count = 0 AND approved_root_resolved_count = universe_node_count THEN 1 ELSE 0 END AS DECIMAL(18, 8)) FROM root_summary CROSS JOIN universe_summary
  UNION ALL SELECT 'display_eligible_count', CAST(display_eligible_count AS DECIMAL(18, 8)) FROM display_summary
  UNION ALL SELECT 'display_reconstructed_count', CAST(display_reconstructed_count AS DECIMAL(18, 8)) FROM display_summary
  UNION ALL SELECT 'display_unresolved_chain_count', CAST(display_unresolved_chain_count AS DECIMAL(18, 8)) FROM display_summary
  UNION ALL SELECT 'display_approved_root_match_count', CAST(display_approved_root_match_count AS DECIMAL(18, 8)) FROM display_summary
  UNION ALL SELECT 'stored_level_comparable_count', CAST(stored_level_comparable_count AS DECIMAL(18, 8)) FROM display_summary
  UNION ALL SELECT 'stored_level_depth_plus_one_match_count', CAST(stored_level_depth_plus_one_match_count AS DECIMAL(18, 8)) FROM display_summary
  UNION ALL SELECT 'stored_level_depth_plus_one_match_rate_percent', CAST(100.0 * stored_level_depth_plus_one_match_count / NULLIF(stored_level_comparable_count, 0) AS DECIMAL(18, 8)) FROM display_summary
  UNION ALL SELECT 'maximum_chain_links', CAST(25 AS DECIMAL(18, 8))
) AS metric

UNION ALL

SELECT
  snapshot_choice.snapshot_date,
  'depth_distribution' AS row_type,
  'display_employee_count' AS metric,
  depth_distribution.depth,
  CAST(depth_distribution.employee_count AS DECIMAL(18, 8)) AS metric_value
FROM snapshot_choice
CROSS JOIN depth_distribution
ORDER BY row_type, depth, metric;
