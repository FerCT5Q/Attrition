-- Aggregate-only display audit for the lower view on the Engineering slide.
--
-- The upper chart uses this exact display denominator:
--   fis_mo_end_dt = 2026-08-23
--   worker_type = 'Employee'
--   employee_type = 'Regular'
--   active_status = 1
--
-- This is intentionally a display-only exception to the historical CTO
-- definition: is_rf360_yes_no is not filtered so that the lower view uses the
-- same universe as eng_or_noneng. Leader IDs are kept inside the query only;
-- the final result contains aggregate metrics and category counts only.
WITH RECURSIVE
snapshot_choice AS (
  SELECT DATE '2026-08-23' AS snapshot_date
),
raw_snapshot AS (
  SELECT
    CAST(employee_id AS VARCHAR(64)) AS employee_id,
    NULLIF(TRIM(CAST(manager_employee_id AS VARCHAR(64))), '') AS manager_employee_id,
    NULLIF(TRIM(CAST(et_leader AS VARCHAR(256))), '') AS et_leader,
    NULLIF(TRIM(CAST(eng_or_noneng AS VARCHAR(128))), '') AS eng_or_noneng
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
    MIN(et_leader) AS canonical_et_leader,
    COUNT(DISTINCT COALESCE(eng_or_noneng, '<NULL>')) AS eng_or_noneng_value_count,
    MIN(eng_or_noneng) AS canonical_eng_or_noneng
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
    eng_or_noneng_value_count,
    canonical_eng_or_noneng AS eng_or_noneng,
    CAST(1 AS INTEGER) AS eligible_flag
  FROM employee_rollup
),
root_anchor AS (
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
    eng_or_noneng_value_count,
    eng_or_noneng,
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
    CAST(1 AS BIGINT) AS eng_or_noneng_value_count,
    CAST(NULL AS VARCHAR(128)) AS eng_or_noneng,
    CAST(0 AS INTEGER) AS eligible_flag
  FROM root_anchor AS r
  LEFT JOIN worker_snapshot AS w
    ON w.employee_id = r.employee_id
  WHERE w.employee_id IS NULL
),
jim_hierarchy (employee_id, depth, visited_path, cycle_flag) AS (
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
  FROM jim_hierarchy AS h
  INNER JOIN worker_snapshot AS child
    ON child.manager_employee_id = h.employee_id
  WHERE h.cycle_flag = 0
    AND h.depth < 100
),
jim_rollup AS (
  SELECT
    walk.employee_id,
    walk.depth,
    walk.noncycle_path_count,
    walk.cycle_row_count,
    walk.maximum_depth,
    SUM(CASE WHEN walk.noncycle_path_count > 0 THEN 1 ELSE 0 END) OVER () AS jim_hierarchy_member_count,
    SUM(CASE WHEN walk.noncycle_path_count > 0 AND walk.depth > 0 THEN walk.noncycle_path_count ELSE 0 END) OVER () AS jim_descendant_path_count,
    SUM(walk.cycle_row_count) OVER () AS jim_cycle_count,
    MAX(walk.maximum_depth) OVER () AS jim_maximum_depth,
    SUM(CASE WHEN walk.maximum_depth >= 100 THEN 1 ELSE 0 END) OVER () AS jim_depth_limit_count,
    SUM(CASE WHEN walk.noncycle_path_count > 1 THEN 1 ELSE 0 END) OVER () AS jim_duplicate_member_count
  FROM (
    SELECT
      employee_id,
      MIN(CASE WHEN cycle_flag = 0 THEN depth END) AS depth,
      SUM(CASE WHEN cycle_flag = 0 THEN 1 ELSE 0 END) AS noncycle_path_count,
      SUM(CASE WHEN cycle_flag = 1 THEN 1 ELSE 0 END) AS cycle_row_count,
      MAX(depth) AS maximum_depth
    FROM jim_hierarchy
    GROUP BY 1
  ) AS walk
),
universe_enriched AS (
  SELECT
    n.employee_id,
    n.eligible_flag,
    n.source_row_count,
    n.manager_assignment_count,
    n.et_leader_value_count,
    n.eng_or_noneng_value_count,
    n.eng_or_noneng,
    CASE WHEN COALESCE(j.noncycle_path_count, 0) > 0 THEN 1 ELSE 0 END AS jim_member_flag,
    CASE
      WHEN n.employee_id = '1200' THEN 1
      WHEN UPPER(TRIM(n.et_leader)) = 'BAAZIZ ACHOUR (1200)' THEN 1
      ELSE 0
    END AS baaziz_member_flag,
    CASE
      WHEN n.employee_id = '1200' THEN 1
      WHEN UPPER(TRIM(n.et_leader)) = 'BAAZIZ ACHOUR (1200)' AND n.employee_id <> '1200' THEN 1
      ELSE 0
    END AS baaziz_et_member_flag,
    CASE WHEN COALESCE(j.noncycle_path_count, 0) > 0 THEN j.depth ELSE NULL END AS jim_depth,
    COALESCE(j.noncycle_path_count, 0) AS jim_noncycle_path_count,
    COALESCE(j.jim_hierarchy_member_count, 0) AS jim_hierarchy_member_count,
    COALESCE(j.jim_descendant_path_count, 0) AS jim_descendant_path_count,
    COALESCE(j.jim_cycle_count, 0) AS jim_cycle_count,
    COALESCE(j.jim_maximum_depth, 0) AS jim_maximum_depth,
    COALESCE(j.jim_depth_limit_count, 0) AS jim_depth_limit_count,
    COALESCE(j.jim_duplicate_member_count, 0) AS jim_duplicate_member_count,
    CASE
      WHEN COALESCE(j.noncycle_path_count, 0) > 0
       OR n.employee_id = '1200'
       OR UPPER(TRIM(n.et_leader)) = 'BAAZIZ ACHOUR (1200)'
      THEN 1 ELSE 0
    END AS cto_member_flag,
    CASE
      WHEN COALESCE(j.noncycle_path_count, 0) > 0
       AND (n.employee_id = '1200' OR UPPER(TRIM(n.et_leader)) = 'BAAZIZ ACHOUR (1200)')
      THEN 1 ELSE 0
    END AS branch_overlap_flag,
    CASE
      WHEN COALESCE(j.noncycle_path_count, 0) > 0
       AND (n.employee_id = '1200' OR UPPER(TRIM(n.et_leader)) = 'BAAZIZ ACHOUR (1200)')
      THEN 1 ELSE 0
    END AS duplicate_branch_membership_flag
  FROM hierarchy_nodes AS n
  LEFT JOIN jim_rollup AS j
    ON j.employee_id = n.employee_id
),
snapshot_summary AS (
  SELECT
    snapshot_choice.snapshot_date,
    COUNT(*) AS eligible_employee_count,
    SUM(source_row_count) AS source_snapshot_row_count,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_source_employee_count,
    SUM(CASE WHEN manager_assignment_count > 1 THEN 1 ELSE 0 END) AS manager_conflict_employee_count,
    SUM(CASE WHEN et_leader_value_count > 1 THEN 1 ELSE 0 END) AS et_leader_conflict_employee_count,
    SUM(CASE WHEN eng_or_noneng_value_count > 1 THEN 1 ELSE 0 END) AS eng_or_noneng_conflict_employee_count,
    SUM(CASE WHEN eng_or_noneng IS NOT NULL THEN 1 ELSE 0 END) AS eng_or_noneng_observable_employee_count,
    SUM(CASE WHEN eng_or_noneng IS NULL THEN 1 ELSE 0 END) AS eng_or_noneng_missing_employee_count,
    COUNT(DISTINCT CASE WHEN eng_or_noneng IS NOT NULL THEN eng_or_noneng END) AS eng_or_noneng_category_count
  FROM worker_snapshot
  CROSS JOIN snapshot_choice
  GROUP BY 1
),
root_summary AS (
  SELECT
    MAX(CASE WHEN employee_id = '892' THEN 1 ELSE 0 END) AS jim_root_present,
    MAX(CASE WHEN employee_id = '1200' THEN 1 ELSE 0 END) AS baaziz_root_present
  FROM regular_snapshot
),
hierarchy_summary AS (
  SELECT
    MAX(jim_hierarchy_member_count) AS jim_hierarchy_member_count,
    MAX(jim_descendant_path_count) AS jim_descendant_path_count,
    MAX(jim_cycle_count) AS jim_cycle_count,
    MAX(jim_maximum_depth) AS jim_maximum_depth,
    MAX(jim_depth_limit_count) AS jim_depth_limit_count,
    MAX(jim_duplicate_member_count) AS jim_duplicate_member_count,
    SUM(CASE WHEN duplicate_branch_membership_flag = 1 THEN 1 ELSE 0 END) AS duplicate_branch_membership_count,
    SUM(CASE WHEN branch_overlap_flag = 1 THEN 1 ELSE 0 END) AS branch_overlap_count,
    SUM(CASE WHEN jim_member_flag = 1 THEN 1 ELSE 0 END) AS jim_branch_count,
    SUM(CASE WHEN baaziz_member_flag = 1 THEN 1 ELSE 0 END) AS baaziz_branch_count,
    SUM(CASE WHEN baaziz_et_member_flag = 1 THEN 1 ELSE 0 END) AS baaziz_et_member_count,
    SUM(CASE WHEN employee_id = '892' AND jim_member_flag = 1 THEN 1 ELSE 0 END) AS jim_leader_in_cto_branch_count,
    SUM(CASE WHEN employee_id = '1200' AND baaziz_member_flag = 1 THEN 1 ELSE 0 END) AS baaziz_leader_in_cto_branch_count,
    SUM(CASE WHEN employee_id = '892' AND eligible_flag = 1 AND cto_member_flag = 1 THEN 1 ELSE 0 END) AS jim_leader_in_eligible_cto_count,
    SUM(CASE WHEN employee_id = '1200' AND eligible_flag = 1 AND cto_member_flag = 1 THEN 1 ELSE 0 END) AS baaziz_leader_in_eligible_cto_count,
    SUM(CASE WHEN eligible_flag = 1 AND cto_member_flag = 1 THEN 1 ELSE 0 END) AS cto_employee_count
  FROM universe_enriched
),
category_counts AS (
  SELECT
    CAST('CTO' AS VARCHAR(64)) AS category,
    SUM(CASE WHEN eligible_flag = 1 AND cto_member_flag = 1 THEN 1 ELSE 0 END) AS employee_count
  FROM universe_enriched
  UNION ALL
  SELECT
    CAST('Corp Fxn & BU' AS VARCHAR(64)) AS category,
    SUM(CASE WHEN eligible_flag = 1 AND cto_member_flag = 0 THEN 1 ELSE 0 END) AS employee_count
  FROM universe_enriched
),
category_summary AS (
  SELECT
    SUM(employee_count) AS category_total_count,
    SUM(CASE WHEN employee_count < 30 THEN 1 ELSE 0 END) AS categories_below_minimum_count,
    MIN(employee_count) AS minimum_category_count,
    SUM(100.0 * employee_count / NULLIF((SELECT eligible_employee_count FROM snapshot_summary), 0)) AS category_percentage_sum
  FROM category_counts
),
metrics AS (
  SELECT snapshot_date, 'eligible_employee_count' AS metric, CAST(eligible_employee_count AS DECIMAL(18, 8)) AS metric_value FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'source_snapshot_row_count', CAST(source_snapshot_row_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'duplicate_source_employee_count', CAST(duplicate_source_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'manager_conflict_employee_count', CAST(manager_conflict_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'et_leader_conflict_employee_count', CAST(et_leader_conflict_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'eng_or_noneng_conflict_employee_count', CAST(eng_or_noneng_conflict_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'eng_or_noneng_observable_employee_count', CAST(eng_or_noneng_observable_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'eng_or_noneng_missing_employee_count', CAST(eng_or_noneng_missing_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'eng_or_noneng_category_count', CAST(eng_or_noneng_category_count AS DECIMAL(18, 8)) FROM snapshot_summary
  UNION ALL SELECT snapshot_date, 'jim_root_present', CAST(root_summary.jim_root_present AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN root_summary
  UNION ALL SELECT snapshot_date, 'baaziz_root_present', CAST(root_summary.baaziz_root_present AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN root_summary
  UNION ALL SELECT snapshot_date, 'jim_hierarchy_member_count', CAST(jim_hierarchy_member_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'jim_descendant_path_count', CAST(jim_descendant_path_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'jim_cycle_count', CAST(jim_cycle_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'jim_maximum_depth', CAST(COALESCE(jim_maximum_depth, 0) AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'jim_duplicate_member_count', CAST(jim_duplicate_member_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'duplicate_branch_membership_count', CAST(duplicate_branch_membership_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'branch_overlap_count', CAST(branch_overlap_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'jim_depth_limit_count', CAST(jim_depth_limit_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'jim_leader_in_cto_branch_count', CAST(jim_leader_in_cto_branch_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'baaziz_leader_in_cto_branch_count', CAST(baaziz_leader_in_cto_branch_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'jim_leader_in_eligible_cto_count', CAST(jim_leader_in_eligible_cto_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'baaziz_leader_in_eligible_cto_count', CAST(baaziz_leader_in_eligible_cto_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'baaziz_et_member_count', CAST(baaziz_et_member_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'jim_branch_count', CAST(jim_branch_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'baaziz_branch_count', CAST(baaziz_branch_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'cto_employee_count', CAST(cto_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN hierarchy_summary
  UNION ALL SELECT snapshot_date, 'category_total_count', CAST(category_total_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN category_summary
  UNION ALL SELECT snapshot_date, 'category_reconciliation_difference', CAST(category_total_count - eligible_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN category_summary
  UNION ALL SELECT snapshot_date, 'categories_below_minimum_count', CAST(categories_below_minimum_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN category_summary
  UNION ALL SELECT snapshot_date, 'minimum_category_count', CAST(minimum_category_count AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN category_summary
  UNION ALL SELECT snapshot_date, 'category_percentage_sum', CAST(category_percentage_sum AS DECIMAL(18, 8)) FROM snapshot_summary CROSS JOIN category_summary
  UNION ALL SELECT snapshot_date, 'eng_or_noneng_denominator_difference', CAST(eligible_employee_count - eng_or_noneng_observable_employee_count AS DECIMAL(18, 8)) FROM snapshot_summary
),
category_rows AS (
  SELECT
    snapshot_summary.snapshot_date,
    category_counts.category,
    category_counts.employee_count,
    CAST(100.0 * category_counts.employee_count / NULLIF(snapshot_summary.eligible_employee_count, 0) AS DECIMAL(18, 8)) AS percentage
  FROM category_counts
  CROSS JOIN snapshot_summary
)
SELECT
  snapshot_date,
  'metric' AS result_type,
  metric,
  CAST(NULL AS VARCHAR(64)) AS category,
  CAST(NULL AS BIGINT) AS employee_count,
  CAST(NULL AS DECIMAL(18, 8)) AS percentage,
  metric_value
FROM metrics

UNION ALL

SELECT
  snapshot_date,
  'category' AS result_type,
  CAST(NULL AS VARCHAR(64)) AS metric,
  category,
  CAST(employee_count AS BIGINT) AS employee_count,
  percentage,
  CAST(NULL AS DECIMAL(18, 8)) AS metric_value
FROM category_rows
ORDER BY 2, 3, 4;
