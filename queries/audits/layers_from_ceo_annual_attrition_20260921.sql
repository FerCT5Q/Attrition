/*
  Slide 32 | manager layers to the CEO | fixed August baseline.

  Population: active Regular Employees at 2025-08-24.
  Category: same-snapshot manager-chain depth to the HR-approved CEO root.
  Outcome: strict VOLUNTARY termination in (2025-08-24, 2026-08-23].

  The approved-root check uses the unique no-manager root with a CEO title at
  this fixed baseline. The identifier is never returned or persisted. All
  returned rows are aggregate-only.
*/
WITH RECURSIVE
params AS (
  SELECT DATE '2025-08-24' AS baseline_date,
         DATE '2026-08-23' AS outcome_cutoff
),
raw_nodes AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    CAST(NULLIF(TRIM(CAST(w.manager_employee_id AS VARCHAR(64))), '') AS BIGINT)
      AS manager_employee_id,
    w.worker_supervisory_organization_level_from_top AS stored_level,
    UPPER(TRIM(CAST(w.job_title AS VARCHAR(512)))) AS normalized_job_title,
    w.worker_type,
    w.employee_type
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_date
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
),
node_rollup AS (
  SELECT
    employee_id,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT COALESCE(CAST(manager_employee_id AS VARCHAR(64)), '<NULL>'))
      AS manager_assignment_count,
    MIN(manager_employee_id) AS canonical_manager_employee_id,
    COUNT(DISTINCT COALESCE(CAST(stored_level AS VARCHAR(64)), '<NULL>'))
      AS stored_level_value_count,
    MIN(stored_level) AS stored_level,
    MAX(CASE
      WHEN normalized_job_title LIKE '%CEO%'
        OR normalized_job_title LIKE '%CHIEF EXECUTIVE OFFICER%'
      THEN 1 ELSE 0
    END) AS ceo_title_flag,
    MAX(CASE
      WHEN worker_type = 'Employee' AND employee_type = 'Regular' THEN 1
      ELSE 0
    END) AS display_employee_flag
  FROM raw_nodes
  GROUP BY 1
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
    ceo_title_flag,
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
    n.employee_id AS origin_employee_id,
    n.display_employee_flag AS origin_display_employee_flag,
    n.stored_level AS origin_stored_level,
    n.employee_id AS current_employee_id,
    n.manager_employee_id AS current_manager_employee_id,
    0 AS reconstructed_depth,
    CAST('|' || CAST(n.employee_id AS VARCHAR(32)) || '|' AS VARCHAR(4096))
      AS visited_path,
    CASE
      WHEN n.manager_assignment_count <> 1 THEN 'manager_conflict'
      WHEN n.manager_employee_id = n.employee_id THEN 'self_manager'
      ELSE NULL
    END AS failure_reason
  FROM nodes n

  UNION ALL

  SELECT
    h.origin_employee_id,
    h.origin_display_employee_flag,
    h.origin_stored_level,
    COALESCE(m.employee_id, h.current_manager_employee_id) AS current_employee_id,
    m.manager_employee_id AS current_manager_employee_id,
    CASE
      WHEN h.reconstructed_depth >= 25 THEN h.reconstructed_depth
      ELSE h.reconstructed_depth + 1
    END AS reconstructed_depth,
    CAST(
      h.visited_path || COALESCE(CAST(m.employee_id AS VARCHAR(32)), '<MISSING>') || '|'
      AS VARCHAR(4096)
    ) AS visited_path,
    CASE
      WHEN h.reconstructed_depth >= 25 THEN 'depth_exceeded'
      WHEN m.employee_id IS NULL THEN 'missing_manager'
      WHEN m.manager_assignment_count <> 1 THEN 'manager_conflict'
      WHEN m.manager_employee_id = m.employee_id THEN 'self_manager'
      WHEN POSITION(
        '|' || CAST(m.employee_id AS VARCHAR(32)) || '|' IN h.visited_path
      ) > 0 THEN 'cycle'
      ELSE NULL
    END AS failure_reason
  FROM hierarchy_walk h
  LEFT JOIN nodes m
    ON m.employee_id = h.current_manager_employee_id
  WHERE h.failure_reason IS NULL
    AND h.current_manager_employee_id IS NOT NULL
),
terminal_ranked AS (
  SELECT
    h.origin_employee_id,
    h.origin_display_employee_flag,
    h.origin_stored_level,
    h.current_employee_id,
    h.current_manager_employee_id,
    h.reconstructed_depth,
    h.visited_path,
    h.failure_reason,
    ROW_NUMBER() OVER (
      PARTITION BY h.origin_employee_id
      ORDER BY h.reconstructed_depth DESC
    ) AS terminal_rank
  FROM hierarchy_walk h
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
  GROUP BY 1
),
root_summary AS (
  SELECT
    COUNT(*) AS root_count,
    COALESCE(MAX(reconstructed_nodes), 0) AS largest_root_node_count
  FROM root_distribution
),
root_reference AS (
  SELECT
    MIN(employee_id) AS approved_root_employee_id,
    COUNT(*) AS approved_root_title_count
  FROM nodes
  WHERE manager_assignment_count = 1
    AND manager_employee_id IS NULL
    AND ceo_title_flag = 1
),
voluntary_events AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    CAST(w.term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > p.baseline_date
    AND CAST(w.term_date AS DATE) <= p.outcome_cutoff
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2
),
display_targets AS (
  SELECT
    t.origin_employee_id AS employee_id,
    t.reconstructed_depth AS depth,
    CASE WHEN v.employee_id IS NULL THEN 0 ELSE 1 END AS voluntary_attrition_target
  FROM terminal t
  LEFT JOIN (
    SELECT DISTINCT employee_id
    FROM voluntary_events
  ) v
    ON v.employee_id = t.origin_employee_id
  WHERE t.reconstructed_flag = 1
    AND t.terminal_root_employee_id = (SELECT approved_root_employee_id FROM root_reference)
    AND t.origin_display_employee_flag = 1
),
depth_distribution AS (
  SELECT
    depth,
    COUNT(*) AS employee_count,
    SUM(voluntary_attrition_target) AS voluntary_exits
  FROM display_targets
  GROUP BY 1
),
metric_rows AS (
  SELECT CAST('active_source_row_count' AS VARCHAR(128)) AS metric, CAST(SUM(source_rows) AS DECIMAL(18,4)) AS metric_value FROM node_rollup
  UNION ALL SELECT 'universe_node_count', CAST(COUNT(*) AS DECIMAL(18,4)) FROM node_rollup
  UNION ALL SELECT 'duplicate_source_node_count', CAST(SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM node_rollup
  UNION ALL SELECT 'manager_conflict_node_count', CAST(SUM(CASE WHEN manager_assignment_count <> 1 THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM node_rollup
  UNION ALL SELECT 'self_manager_node_count', CAST(SUM(CASE WHEN manager_assignment_count = 1 AND canonical_manager_employee_id = employee_id THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM node_rollup
  UNION ALL SELECT 'stored_level_conflict_node_count', CAST(SUM(CASE WHEN stored_level_value_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM node_rollup
  UNION ALL SELECT 'reconstructed_count', CAST(SUM(reconstructed_flag) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'unresolved_chain_count', CAST(SUM(CASE WHEN reconstructed_flag = 0 THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'missing_manager_chain_count', CAST(SUM(CASE WHEN failure_reason = 'missing_manager' THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'self_manager_chain_count', CAST(SUM(CASE WHEN failure_reason = 'self_manager' THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'cycle_chain_count', CAST(SUM(CASE WHEN failure_reason = 'cycle' THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'depth_exceeded_chain_count', CAST(SUM(CASE WHEN failure_reason = 'depth_exceeded' THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'manager_conflict_chain_count', CAST(SUM(CASE WHEN failure_reason = 'manager_conflict' THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'root_count', CAST(MAX(root_count) AS DECIMAL(18,4)) FROM root_summary
  UNION ALL SELECT 'approved_root_resolved_count', CAST(SUM(CASE WHEN reconstructed_flag = 1 AND terminal_root_employee_id = (SELECT approved_root_employee_id FROM root_reference) THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'nonmatching_approved_root_count', CAST(SUM(CASE WHEN reconstructed_flag = 1 AND terminal_root_employee_id <> (SELECT approved_root_employee_id FROM root_reference) THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'maximum_observed_depth', CAST(MAX(reconstructed_depth) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'convergence_rate_percent', CAST(100.0 * MAX(largest_root_node_count) / NULLIF(SUM(reconstructed_flag), 0) AS DECIMAL(18,8)) FROM terminal CROSS JOIN root_summary
  UNION ALL SELECT 'root_reference_pass', CAST(CASE WHEN MAX(root_count) = 1 AND (SELECT approved_root_title_count FROM root_reference) = 1 AND MAX(largest_root_node_count) = SUM(reconstructed_flag) AND SUM(CASE WHEN reconstructed_flag = 1 AND terminal_root_employee_id = (SELECT approved_root_employee_id FROM root_reference) THEN 1 ELSE 0 END) = SUM(reconstructed_flag) THEN 1 ELSE 0 END AS DECIMAL(18,4)) FROM terminal CROSS JOIN root_summary
  UNION ALL SELECT 'display_eligible_count', CAST(SUM(CASE WHEN origin_display_employee_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'display_reconstructed_count', CAST(SUM(CASE WHEN origin_display_employee_flag = 1 AND reconstructed_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'display_unresolved_chain_count', CAST(SUM(CASE WHEN origin_display_employee_flag = 1 AND reconstructed_flag = 0 THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'display_approved_root_match_count', CAST(SUM(CASE WHEN origin_display_employee_flag = 1 AND reconstructed_flag = 1 AND terminal_root_employee_id = (SELECT approved_root_employee_id FROM root_reference) THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'stored_level_comparable_count', CAST(SUM(CASE WHEN origin_display_employee_flag = 1 AND reconstructed_flag = 1 AND origin_stored_level IS NOT NULL THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'stored_level_depth_plus_one_match_count', CAST(SUM(CASE WHEN origin_display_employee_flag = 1 AND reconstructed_flag = 1 AND origin_stored_level IS NOT NULL AND origin_stored_level = reconstructed_depth + 1 THEN 1 ELSE 0 END) AS DECIMAL(18,4)) FROM terminal
  UNION ALL SELECT 'stored_level_depth_plus_one_match_rate_percent', CAST(100.0 * SUM(CASE WHEN origin_display_employee_flag = 1 AND reconstructed_flag = 1 AND origin_stored_level IS NOT NULL AND origin_stored_level = reconstructed_depth + 1 THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN origin_display_employee_flag = 1 AND reconstructed_flag = 1 AND origin_stored_level IS NOT NULL THEN 1 ELSE 0 END), 0) AS DECIMAL(18,8)) FROM terminal
  UNION ALL SELECT 'maximum_chain_links', CAST(25 AS DECIMAL(18,4))
  UNION ALL SELECT 'baseline_voluntary_exits', CAST(SUM(voluntary_attrition_target) AS DECIMAL(18,4)) FROM display_targets
  UNION ALL SELECT 'voluntary_source_distinct_employee_count', CAST((SELECT COUNT(DISTINCT employee_id) FROM voluntary_events) AS DECIMAL(18,4))
)
SELECT
  CAST('metric' AS VARCHAR(32)) AS row_type,
  metric,
  CAST(NULL AS INTEGER) AS depth,
  metric_value,
  CAST(NULL AS BIGINT) AS employee_count,
  CAST(NULL AS BIGINT) AS voluntary_exits,
  CAST(NULL AS DECIMAL(18,8)) AS annual_attrition_rate_percent
FROM metric_rows
UNION ALL
SELECT
  CAST('depth_distribution' AS VARCHAR(32)) AS row_type,
  CAST('display_employee_count' AS VARCHAR(128)) AS metric,
  depth,
  CAST(NULL AS DECIMAL(18,8)) AS metric_value,
  employee_count,
  voluntary_exits,
  100.0 * voluntary_exits / NULLIF(employee_count, 0) AS annual_attrition_rate_percent
FROM depth_distribution
ORDER BY row_type, metric, depth;
