-- Aggregate-only diagnostic for the two-leader CTO display definition.
--
-- Claim: a current active Regular Employee snapshot must contain a
-- reconstructible Jim branch and both documented leaders must be represented
-- in the eligible CTO population before the lower display is published.
--
-- Acceptance rule:
--   * Jim root exists and is eligible, or the documented root exception is
--     explicitly explained;
--   * active Jim descendants are reconstructible by same-snapshot
--     manager_employee_id;
--   * no cycles, depth-limit paths, duplicate paths, or branch overlap remain;
--   * Baaziz's ET branch and leader presence are quantified separately.
-- Only counts and flags are returned; IDs and names stay inside the query.
WITH RECURSIVE
snapshot_choice AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
regular_source AS (
    SELECT
        CAST(employee_id AS VARCHAR(64)) AS employee_id,
        active_status,
        NULLIF(TRIM(CAST(manager_employee_id AS VARCHAR(64))), '') AS manager_employee_id,
        NULLIF(TRIM(CAST(et_leader AS VARCHAR(256))), '') AS et_leader,
        NULLIF(TRIM(CAST(is_rf360_yes_no AS VARCHAR(64))), '') AS rf360_value
    FROM hrda.post_hire_monthly_worker_dtls
    CROSS JOIN snapshot_choice
    WHERE fis_mo_end_dt = snapshot_choice.snapshot_date
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND employee_id IS NOT NULL
),
regular_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS source_row_count,
        MAX(CASE WHEN active_status = 1 THEN 1 ELSE 0 END) AS active_flag,
        COUNT(DISTINCT COALESCE(manager_employee_id, '<NULL>')) AS manager_assignment_count,
        MIN(manager_employee_id) AS canonical_manager_employee_id,
        MAX(CASE WHEN rf360_value = '0' THEN 1 ELSE 0 END) AS rf360_zero_flag,
        MAX(CASE WHEN UPPER(TRIM(et_leader)) = 'JIM THOMPSON (892)' THEN 1 ELSE 0 END) AS jim_et_flag,
        MAX(CASE WHEN UPPER(TRIM(et_leader)) = 'BAAZIZ ACHOUR (1200)' THEN 1 ELSE 0 END) AS baaziz_et_flag
    FROM regular_source
    GROUP BY 1
),
regular_snapshot AS (
    SELECT
        employee_id,
        source_row_count,
        active_flag,
        CASE WHEN manager_assignment_count = 1 THEN canonical_manager_employee_id ELSE NULL END AS manager_employee_id,
        manager_assignment_count,
        rf360_zero_flag,
        jim_et_flag,
        baaziz_et_flag
    FROM regular_employee
),
root_anchor AS (
    SELECT CAST('892' AS VARCHAR(64)) AS employee_id
),
hierarchy_nodes AS (
    SELECT
        employee_id,
        source_row_count,
        active_flag,
        manager_employee_id,
        manager_assignment_count,
        rf360_zero_flag,
        jim_et_flag,
        baaziz_et_flag
    FROM regular_snapshot

    UNION ALL

    SELECT
        root_anchor.employee_id,
        CAST(0 AS BIGINT) AS source_row_count,
        CAST(0 AS INTEGER) AS active_flag,
        CAST(NULL AS VARCHAR(64)) AS manager_employee_id,
        CAST(1 AS BIGINT) AS manager_assignment_count,
        CAST(0 AS INTEGER) AS rf360_zero_flag,
        CAST(0 AS INTEGER) AS jim_et_flag,
        CAST(0 AS INTEGER) AS baaziz_et_flag
    FROM root_anchor
    LEFT JOIN regular_snapshot
      ON regular_snapshot.employee_id = root_anchor.employee_id
    WHERE regular_snapshot.employee_id IS NULL
),
jim_walk (employee_id, depth, visited_path, cycle_flag) AS (
    SELECT
        hierarchy_nodes.employee_id,
        CAST(0 AS INTEGER) AS depth,
        CAST('|' || hierarchy_nodes.employee_id || '|' AS VARCHAR(65535)) AS visited_path,
        CAST(0 AS INTEGER) AS cycle_flag
    FROM hierarchy_nodes
    WHERE hierarchy_nodes.employee_id = '892'

    UNION ALL

    SELECT
        child.employee_id,
        jim_walk.depth + 1,
        CAST(jim_walk.visited_path || child.employee_id || '|' AS VARCHAR(65535)),
        CASE
            WHEN POSITION('|' || child.employee_id || '|' IN jim_walk.visited_path) > 0 THEN 1
            ELSE 0
        END AS cycle_flag
    FROM jim_walk
    INNER JOIN regular_snapshot AS child
      ON child.manager_employee_id = jim_walk.employee_id
    WHERE jim_walk.cycle_flag = 0
      AND jim_walk.depth < 100
),
jim_member_rollup AS (
    SELECT
        walk.employee_id,
        MIN(CASE WHEN walk.cycle_flag = 0 THEN walk.depth END) AS depth,
        SUM(CASE WHEN walk.cycle_flag = 0 THEN 1 ELSE 0 END) AS noncycle_path_count,
        SUM(CASE WHEN walk.cycle_flag = 1 THEN 1 ELSE 0 END) AS cycle_row_count,
        MAX(walk.depth) AS maximum_depth
    FROM jim_walk AS walk
    GROUP BY 1
),
jim_members AS (
    SELECT
        rollup.employee_id,
        rollup.depth,
        rollup.noncycle_path_count,
        rollup.cycle_row_count,
        rollup.maximum_depth,
        COALESCE(snap_row.active_flag, 0) AS active_flag,
        COALESCE(snap_row.rf360_zero_flag, 0) AS rf360_zero_flag
    FROM jim_member_rollup AS rollup
    LEFT JOIN regular_snapshot AS snap_row
      ON snap_row.employee_id = rollup.employee_id
    WHERE rollup.noncycle_path_count > 0
),
baaziz_members AS (
    SELECT employee_id
    FROM regular_snapshot
    WHERE employee_id = '1200'
       OR baaziz_et_flag = 1
),
overlap AS (
    SELECT COUNT(*) AS overlap_count
    FROM jim_members
    INNER JOIN baaziz_members
      ON baaziz_members.employee_id = jim_members.employee_id
),
metrics AS (
    SELECT 'regular_employee_count' AS metric, CAST(COUNT(*) AS DECIMAL(18, 8)) AS metric_value FROM regular_snapshot
    UNION ALL SELECT 'active_regular_employee_count', CAST(SUM(active_flag) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'active_regular_rf360_zero_employee_count', CAST(SUM(CASE WHEN active_flag = 1 AND rf360_zero_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'regular_duplicate_employee_count', CAST(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'regular_manager_conflict_employee_count', CAST(SUM(CASE WHEN manager_assignment_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'regular_manager_null_employee_count', CAST(SUM(CASE WHEN manager_employee_id IS NULL THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'active_regular_manager_null_employee_count', CAST(SUM(CASE WHEN active_flag = 1 AND manager_employee_id IS NULL THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'jim_root_present_count', CAST(SUM(CASE WHEN employee_id = '892' THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'jim_root_active_count', CAST(SUM(CASE WHEN employee_id = '892' AND active_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'baaziz_root_present_count', CAST(SUM(CASE WHEN employee_id = '1200' THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'baaziz_root_active_count', CAST(SUM(CASE WHEN employee_id = '1200' AND active_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'jim_direct_report_regular_count', CAST(SUM(CASE WHEN manager_employee_id = '892' THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'jim_direct_report_active_count', CAST(SUM(CASE WHEN manager_employee_id = '892' AND active_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'jim_et_leader_regular_count', CAST(SUM(jim_et_flag) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'jim_et_leader_active_count', CAST(SUM(CASE WHEN jim_et_flag = 1 AND active_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'baaziz_et_member_regular_count', CAST(SUM(CASE WHEN baaziz_et_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'baaziz_et_member_active_count', CAST(SUM(CASE WHEN baaziz_et_flag = 1 AND active_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM regular_snapshot
    UNION ALL SELECT 'jim_reachable_regular_count', CAST(COUNT(*) AS DECIMAL(18, 8)) FROM jim_members
    UNION ALL SELECT 'jim_reachable_active_count', CAST(SUM(active_flag) AS DECIMAL(18, 8)) FROM jim_members
    UNION ALL SELECT 'jim_descendant_regular_count', CAST(SUM(CASE WHEN depth > 0 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM jim_members
    UNION ALL SELECT 'jim_descendant_active_count', CAST(SUM(CASE WHEN depth > 0 AND active_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM jim_members
    UNION ALL SELECT 'jim_cycle_row_count', CAST(SUM(cycle_row_count) AS DECIMAL(18, 8)) FROM jim_member_rollup
    UNION ALL SELECT 'jim_duplicate_path_employee_count', CAST(SUM(CASE WHEN noncycle_path_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM jim_member_rollup
    UNION ALL SELECT 'jim_depth_limit_employee_count', CAST(SUM(CASE WHEN maximum_depth >= 100 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM jim_member_rollup
    UNION ALL SELECT 'jim_baaziz_branch_overlap_count', CAST(overlap.overlap_count AS DECIMAL(18, 8)) FROM overlap
    UNION ALL SELECT 'jim_root_in_active_cto_count', CAST(SUM(CASE WHEN employee_id = '892' AND active_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM jim_members
    UNION ALL SELECT 'baaziz_root_in_active_cto_count', CAST(SUM(CASE WHEN employee_id = '1200' AND active_flag = 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM baaziz_members INNER JOIN regular_snapshot USING (employee_id)
)
SELECT snapshot_choice.snapshot_date, metrics.metric, metrics.metric_value
FROM metrics
CROSS JOIN snapshot_choice
ORDER BY metrics.metric;
