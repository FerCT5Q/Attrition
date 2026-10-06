-- Aggregate-only audit for annual voluntary attrition in the documented
-- CTO versus Corp Fxn & BU organizational split used on slide 15.
--
-- Deliverable mode: internal_analysis. Employee IDs are used only inside
-- same-snapshot hierarchy reconstruction and outcome joins; the final result
-- returns category-level counts, rates, and aggregate validation metrics.
--
-- Claim: for active regular employees at the 2025-07-27 snapshot, classify
-- CTO membership using the documented two-branch organizational rule and
-- measure whether each cohort member had a voluntary termination in the next
-- 12 months. The annual outcome window is (2025-07-27, 2026-07-27].
--
-- Acceptance rule: both categories have n >= 30; categories reconcile to the
-- eligible baseline; the two branch anchors are available; no duplicate
-- employee, manager, or ET-leader conflict exists in the baseline; and the
-- hierarchy has no cycle, depth-limit, duplicate-path, or branch-overlap row.
WITH RECURSIVE
snapshot_choice AS (
  SELECT DATE '2025-07-27' AS snapshot_date
),
raw_snapshot AS (
  SELECT
    CAST(employee_id AS VARCHAR(64)) AS employee_id,
    NULLIF(TRIM(CAST(manager_employee_id AS VARCHAR(64))), '') AS manager_employee_id,
    NULLIF(TRIM(CAST(et_leader AS VARCHAR(256))), '') AS et_leader
  FROM hrda.post_hire_monthly_worker_dtls
  CROSS JOIN snapshot_choice
  WHERE fis_mo_end_dt = snapshot_choice.snapshot_date
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
),
regular_snapshot AS (
  SELECT
    CAST(employee_id AS VARCHAR(64)) AS employee_id,
    COUNT(*) AS source_row_count
  FROM hrda.post_hire_monthly_worker_dtls
  CROSS JOIN snapshot_choice
  WHERE fis_mo_end_dt = snapshot_choice.snapshot_date
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND employee_id IS NOT NULL
  GROUP BY 1
),
employee_rollup AS (
  SELECT
    employee_id,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT COALESCE(manager_employee_id, '<NULL>')) AS manager_assignment_count,
    MIN(manager_employee_id) AS canonical_manager_employee_id,
    COUNT(DISTINCT COALESCE(et_leader, '<NULL>')) AS et_leader_value_count,
    MIN(et_leader) AS canonical_et_leader
  FROM raw_snapshot
  GROUP BY 1
),
worker_snapshot AS (
  SELECT
    employee_id,
    source_row_count,
    manager_assignment_count,
    CASE
      WHEN manager_assignment_count = 1 THEN canonical_manager_employee_id
      ELSE NULL
    END AS manager_employee_id,
    et_leader_value_count,
    canonical_et_leader AS et_leader,
    CAST(1 AS INTEGER) AS eligible_flag
  FROM employee_rollup
),
root_anchor_a AS (
  SELECT CAST('892' AS VARCHAR(64)) AS employee_id
),
hierarchy_nodes AS (
  SELECT
    employee_id,
    source_row_count,
    manager_assignment_count,
    manager_employee_id,
    et_leader_value_count,
    et_leader,
    eligible_flag
  FROM worker_snapshot

  UNION ALL

  SELECT
    r.employee_id,
    CAST(0 AS BIGINT) AS source_row_count,
    CAST(1 AS BIGINT) AS manager_assignment_count,
    CAST(NULL AS VARCHAR(64)) AS manager_employee_id,
    CAST(1 AS BIGINT) AS et_leader_value_count,
    CAST(NULL AS VARCHAR(256)) AS et_leader,
    CAST(0 AS INTEGER) AS eligible_flag
  FROM root_anchor_a AS r
  LEFT JOIN worker_snapshot AS w
    ON w.employee_id = r.employee_id
  WHERE w.employee_id IS NULL
),
branch_a_hierarchy (employee_id, depth, visited_path, cycle_flag) AS (
  SELECT
    n.employee_id,
    CAST(0 AS INTEGER) AS depth,
    CAST('|' || n.employee_id || '|' AS VARCHAR(65535)) AS visited_path,
    CAST(0 AS INTEGER) AS cycle_flag
  FROM hierarchy_nodes AS n
  WHERE n.employee_id = '892'

  UNION ALL

  SELECT
    child.employee_id,
    h.depth + 1,
    CAST(h.visited_path || child.employee_id || '|' AS VARCHAR(65535)),
    CASE
      WHEN POSITION('|' || child.employee_id || '|' IN h.visited_path) > 0 THEN 1
      ELSE 0
    END AS cycle_flag
  FROM branch_a_hierarchy AS h
  INNER JOIN worker_snapshot AS child
    ON child.manager_employee_id = h.employee_id
  WHERE h.cycle_flag = 0
    AND h.depth < 100
),
branch_a_rollup AS (
  SELECT
    walk.employee_id,
    walk.depth,
    walk.noncycle_path_count,
    walk.cycle_row_count,
    walk.maximum_depth,
    SUM(CASE WHEN walk.noncycle_path_count > 0 THEN 1 ELSE 0 END) OVER () AS branch_a_member_count,
    SUM(CASE WHEN walk.noncycle_path_count > 0 AND walk.depth > 0 THEN walk.noncycle_path_count ELSE 0 END) OVER () AS branch_a_descendant_path_count,
    SUM(walk.cycle_row_count) OVER () AS branch_a_cycle_count,
    MAX(walk.maximum_depth) OVER () AS branch_a_maximum_depth,
    SUM(CASE WHEN walk.maximum_depth >= 100 THEN 1 ELSE 0 END) OVER () AS branch_a_depth_limit_count,
    SUM(CASE WHEN walk.noncycle_path_count > 1 THEN 1 ELSE 0 END) OVER () AS branch_a_duplicate_member_count
  FROM (
    SELECT
      employee_id,
      MIN(CASE WHEN cycle_flag = 0 THEN depth END) AS depth,
      SUM(CASE WHEN cycle_flag = 0 THEN 1 ELSE 0 END) AS noncycle_path_count,
      SUM(CASE WHEN cycle_flag = 1 THEN 1 ELSE 0 END) AS cycle_row_count,
      MAX(depth) AS maximum_depth
    FROM branch_a_hierarchy
    GROUP BY 1
  ) AS walk
),
root_anchor_b AS (
  SELECT
    MAX(CASE WHEN employee_id = '1200' THEN employee_id END) AS employee_id,
    MAX(CASE WHEN employee_id = '1200' THEN et_leader END) AS et_leader,
    MAX(CASE WHEN employee_id = '1200' THEN 1 ELSE 0 END) AS active_present
  FROM worker_snapshot
),
universe_enriched AS (
  SELECT
    n.employee_id,
    n.eligible_flag,
    n.source_row_count,
    n.manager_assignment_count,
    n.et_leader_value_count,
    CASE WHEN COALESCE(a.noncycle_path_count, 0) > 0 THEN 1 ELSE 0 END AS branch_a_member_flag,
    CASE
      WHEN n.employee_id = b.employee_id THEN 1
      WHEN b.et_leader IS NOT NULL
       AND UPPER(TRIM(n.et_leader)) = UPPER(TRIM(b.et_leader)) THEN 1
      ELSE 0
    END AS branch_b_member_flag,
    CASE WHEN COALESCE(a.noncycle_path_count, 0) > 0 THEN a.depth ELSE NULL END AS branch_a_depth,
    COALESCE(a.noncycle_path_count, 0) AS branch_a_noncycle_path_count,
    COALESCE(a.branch_a_member_count, 0) AS branch_a_hierarchy_member_count,
    COALESCE(a.branch_a_descendant_path_count, 0) AS branch_a_descendant_path_count,
    COALESCE(a.branch_a_cycle_count, 0) AS branch_a_cycle_count,
    COALESCE(a.branch_a_maximum_depth, 0) AS branch_a_maximum_depth,
    COALESCE(a.branch_a_depth_limit_count, 0) AS branch_a_depth_limit_count,
    COALESCE(a.branch_a_duplicate_member_count, 0) AS branch_a_duplicate_member_count,
    CASE
      WHEN COALESCE(a.noncycle_path_count, 0) > 0
       OR n.employee_id = b.employee_id
       OR (b.et_leader IS NOT NULL AND UPPER(TRIM(n.et_leader)) = UPPER(TRIM(b.et_leader)))
      THEN 1 ELSE 0
    END AS cto_member_flag,
    CASE
      WHEN COALESCE(a.noncycle_path_count, 0) > 0
       AND (n.employee_id = b.employee_id OR (b.et_leader IS NOT NULL AND UPPER(TRIM(n.et_leader)) = UPPER(TRIM(b.et_leader))))
      THEN 1 ELSE 0
    END AS branch_overlap_flag
  FROM hierarchy_nodes AS n
  CROSS JOIN root_anchor_b AS b
  LEFT JOIN branch_a_rollup AS a
    ON a.employee_id = n.employee_id
),
voluntary_event_source AS (
  SELECT
    CAST(employee_id AS VARCHAR(64)) AS employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  CROSS JOIN snapshot_choice
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND term_date > snapshot_choice.snapshot_date
    AND term_date <= DATEADD(year, 1, snapshot_choice.snapshot_date)
),
voluntary_events AS (
  SELECT
    employee_id,
    COUNT(*) AS voluntary_event_source_row_count,
    COUNT(DISTINCT term_date) AS voluntary_event_date_count
  FROM voluntary_event_source
  GROUP BY 1
),
category_outcomes AS (
  SELECT
    CAST('CTO' AS VARCHAR(64)) AS category,
    SUM(CASE WHEN u.eligible_flag = 1 AND u.cto_member_flag = 1 THEN 1 ELSE 0 END) AS eligible_employee_count,
    SUM(CASE WHEN u.eligible_flag = 1 AND u.cto_member_flag = 1 AND e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count
  FROM universe_enriched AS u
  LEFT JOIN voluntary_events AS e
    ON e.employee_id = u.employee_id

  UNION ALL

  SELECT
    CAST('Corp Fxn & BU' AS VARCHAR(64)) AS category,
    SUM(CASE WHEN u.eligible_flag = 1 AND u.cto_member_flag = 0 THEN 1 ELSE 0 END) AS eligible_employee_count,
    SUM(CASE WHEN u.eligible_flag = 1 AND u.cto_member_flag = 0 AND e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count
  FROM universe_enriched AS u
  LEFT JOIN voluntary_events AS e
    ON e.employee_id = u.employee_id
),
snapshot_summary AS (
  SELECT
    snapshot_choice.snapshot_date,
    COUNT(*) AS eligible_employee_count,
    SUM(source_row_count) AS source_snapshot_row_count,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_source_employee_count,
    SUM(CASE WHEN manager_assignment_count > 1 THEN 1 ELSE 0 END) AS manager_conflict_employee_count,
    SUM(CASE WHEN et_leader_value_count > 1 THEN 1 ELSE 0 END) AS et_leader_conflict_employee_count
  FROM worker_snapshot
  CROSS JOIN snapshot_choice
  GROUP BY 1
),
root_summary AS (
  SELECT
    MAX(CASE WHEN employee_id = '892' THEN 1 ELSE 0 END) AS branch_a_root_present
  FROM regular_snapshot
),
hierarchy_summary AS (
  SELECT
    MAX(branch_a_hierarchy_member_count) AS branch_a_hierarchy_member_count,
    MAX(branch_a_descendant_path_count) AS branch_a_descendant_path_count,
    MAX(branch_a_cycle_count) AS branch_a_cycle_count,
    MAX(branch_a_maximum_depth) AS branch_a_maximum_depth,
    MAX(branch_a_depth_limit_count) AS branch_a_depth_limit_count,
    MAX(branch_a_duplicate_member_count) AS branch_a_duplicate_member_count,
    SUM(CASE WHEN branch_overlap_flag = 1 THEN 1 ELSE 0 END) AS branch_overlap_count,
    SUM(CASE WHEN branch_a_member_flag = 1 THEN 1 ELSE 0 END) AS branch_a_count,
    SUM(CASE WHEN branch_b_member_flag = 1 THEN 1 ELSE 0 END) AS branch_b_count,
    SUM(CASE WHEN eligible_flag = 1 AND cto_member_flag = 1 THEN 1 ELSE 0 END) AS cto_employee_count
  FROM universe_enriched
),
event_summary AS (
  SELECT
    COUNT(*) AS voluntary_event_employee_count,
    COALESCE(SUM(voluntary_event_source_row_count), 0) AS voluntary_event_source_row_count,
    COALESCE(SUM(CASE WHEN voluntary_event_date_count > 1 THEN 1 ELSE 0 END), 0) AS voluntary_employee_multiple_term_date_count
  FROM voluntary_events
),
category_summary AS (
  SELECT
    SUM(eligible_employee_count) AS category_total_count,
    SUM(CASE WHEN eligible_employee_count < 30 THEN 1 ELSE 0 END) AS categories_below_minimum_count,
    MIN(eligible_employee_count) AS minimum_category_count,
    SUM(voluntary_exit_count) AS total_voluntary_exit_count
  FROM category_outcomes
),
metrics AS (
  SELECT snapshot_date, 'eligible_employee_count' AS metric, CAST(eligible_employee_count AS DECIMAL(18, 8)) AS metric_value FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'source_snapshot_row_count', CAST(source_snapshot_row_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'duplicate_source_employee_count', CAST(duplicate_source_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'manager_conflict_employee_count', CAST(manager_conflict_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'et_leader_conflict_employee_count', CAST(et_leader_conflict_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'branch_a_root_present', CAST(root_summary.branch_a_root_present AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN root_summary
  UNION ALL SELECT snapshot_date, 'branch_b_active_present', CAST(root_anchor_b.active_present AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN root_anchor_b
  UNION ALL SELECT snapshot_date, 'branch_a_hierarchy_member_count', CAST(hierarchy_summary.branch_a_hierarchy_member_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'branch_a_descendant_path_count', CAST(hierarchy_summary.branch_a_descendant_path_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'branch_a_cycle_count', CAST(hierarchy_summary.branch_a_cycle_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'branch_a_maximum_depth', CAST(COALESCE(hierarchy_summary.branch_a_maximum_depth, 0) AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'branch_a_duplicate_member_count', CAST(hierarchy_summary.branch_a_duplicate_member_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'branch_a_depth_limit_count', CAST(hierarchy_summary.branch_a_depth_limit_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'branch_overlap_count', CAST(hierarchy_summary.branch_overlap_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'branch_a_count', CAST(hierarchy_summary.branch_a_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'branch_b_count', CAST(hierarchy_summary.branch_b_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'cto_employee_count', CAST(hierarchy_summary.cto_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'voluntary_event_employee_count', CAST(event_summary.voluntary_event_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN event_summary
  UNION ALL SELECT snapshot_date, 'voluntary_event_source_row_count', CAST(event_summary.voluntary_event_source_row_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN event_summary
  UNION ALL SELECT snapshot_date, 'voluntary_employee_multiple_term_date_count', CAST(event_summary.voluntary_employee_multiple_term_date_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN event_summary
  UNION ALL SELECT snapshot_date, 'category_total_count', CAST(category_summary.category_total_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN category_summary
  UNION ALL SELECT snapshot_date, 'category_reconciliation_difference', CAST(category_summary.category_total_count - snapshot_summary.eligible_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN category_summary
  UNION ALL SELECT snapshot_date, 'categories_below_minimum_count', CAST(category_summary.categories_below_minimum_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN category_summary
  UNION ALL SELECT snapshot_date, 'minimum_category_count', CAST(category_summary.minimum_category_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN category_summary
  UNION ALL SELECT snapshot_date, 'total_voluntary_exit_count', CAST(category_summary.total_voluntary_exit_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN category_summary
),
category_rows AS (
  SELECT
    snapshot_summary.snapshot_date,
    category_outcomes.category,
    category_outcomes.eligible_employee_count,
    category_outcomes.voluntary_exit_count,
    CAST(100.0 * category_outcomes.voluntary_exit_count / NULLIF(category_outcomes.eligible_employee_count, 0) AS DECIMAL(18, 8)) AS annual_attrition_rate_percent
  FROM category_outcomes
  CROSS JOIN snapshot_summary
)
SELECT
  snapshot_date,
  'metric' AS result_type,
  metric,
  CAST(NULL AS VARCHAR(64)) AS category,
  CAST(NULL AS BIGINT) AS eligible_employee_count,
  CAST(NULL AS BIGINT) AS voluntary_exit_count,
  CAST(NULL AS DECIMAL(18, 8)) AS annual_attrition_rate_percent,
  metric_value
FROM metrics

UNION ALL

SELECT
  snapshot_date,
  'category' AS result_type,
  CAST(NULL AS VARCHAR(64)) AS metric,
  category,
  CAST(eligible_employee_count AS BIGINT) AS eligible_employee_count,
  CAST(voluntary_exit_count AS BIGINT) AS voluntary_exit_count,
  annual_attrition_rate_percent,
  CAST(NULL AS DECIMAL(18, 8)) AS metric_value
FROM category_rows
ORDER BY 2, 3, 4;
