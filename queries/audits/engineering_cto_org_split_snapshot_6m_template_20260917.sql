/* Aggregate-only template. {{SNAPSHOT_DATE}} is replaced by the controlled runner. */
WITH RECURSIVE
snapshot_choice AS (SELECT DATE '{{SNAPSHOT_DATE}}' AS snapshot_date),
raw_snapshot AS (
  SELECT CAST(w.employee_id AS VARCHAR(64)) AS employee_id,
         NULLIF(TRIM(CAST(w.manager_employee_id AS VARCHAR(64))), '') AS manager_employee_id,
         NULLIF(TRIM(CAST(w.et_leader AS VARCHAR(256))), '') AS et_leader
  FROM hrda.post_hire_monthly_worker_dtls AS w CROSS JOIN snapshot_choice AS s
  WHERE CAST(w.fis_mo_end_dt AS DATE) = s.snapshot_date AND w.worker_type='Employee'
    AND w.employee_type='Regular' AND w.active_status=1 AND w.employee_id IS NOT NULL
),
worker_snapshot AS (
  SELECT employee_id, COUNT(*) AS source_row_count,
         COUNT(DISTINCT COALESCE(manager_employee_id, '<NULL>')) AS manager_assignment_count,
         MIN(manager_employee_id) AS manager_employee_id,
         COUNT(DISTINCT COALESCE(et_leader, '<NULL>')) AS et_leader_value_count,
         MIN(et_leader) AS et_leader
  FROM raw_snapshot GROUP BY 1
),
root_anchor AS (SELECT CAST('892' AS VARCHAR(64)) AS employee_id),
hierarchy_nodes AS (
  SELECT employee_id, manager_employee_id FROM worker_snapshot
  UNION ALL
  SELECT r.employee_id, CAST(NULL AS VARCHAR(64))
  FROM root_anchor AS r LEFT JOIN worker_snapshot AS w ON w.employee_id=r.employee_id
  WHERE w.employee_id IS NULL
),
jim_hierarchy (employee_id, depth, visited_path, cycle_flag) AS (
  SELECT n.employee_id, CAST(0 AS INTEGER), CAST('|'||n.employee_id||'|' AS VARCHAR(65535)), CAST(0 AS INTEGER)
  FROM hierarchy_nodes AS n WHERE n.employee_id='892'
  UNION ALL
  SELECT child.employee_id, h.depth+1, CAST(h.visited_path||child.employee_id||'|' AS VARCHAR(65535)),
         CASE WHEN POSITION('|'||child.employee_id||'|' IN h.visited_path)>0 THEN 1 ELSE 0 END
  FROM jim_hierarchy AS h INNER JOIN worker_snapshot AS child ON child.manager_employee_id=h.employee_id
  WHERE h.cycle_flag=0 AND h.depth<100
),
anchor_a_rollup AS (
  SELECT employee_id, SUM(CASE WHEN cycle_flag=0 THEN 1 ELSE 0 END) AS noncycle_path_count,
         SUM(CASE WHEN cycle_flag=1 THEN 1 ELSE 0 END) AS cycle_row_count, MAX(depth) AS maximum_depth
  FROM jim_hierarchy GROUP BY 1
),
anchor_b_reference AS (
  SELECT MIN(NULLIF(TRIM(CAST(et_leader AS VARCHAR(256))), '')) AS anchor_b_et_leader,
         COUNT(DISTINCT NULLIF(TRIM(CAST(et_leader AS VARCHAR(256))), '')) AS anchor_b_et_leader_value_count
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(employee_id AS VARCHAR(64))='1200' AND worker_type='Employee' AND employee_type='Regular'
),
mapped_snapshot AS (
  SELECT w.employee_id, w.source_row_count, w.manager_assignment_count, w.et_leader_value_count,
         CASE WHEN COALESCE(a.noncycle_path_count,0)>0 THEN 1 ELSE 0 END AS anchor_a_member_flag,
         CASE WHEN w.employee_id='1200' OR (b.anchor_b_et_leader IS NOT NULL AND UPPER(TRIM(w.et_leader))=UPPER(TRIM(b.anchor_b_et_leader))) THEN 1 ELSE 0 END AS anchor_b_member_flag,
         CASE WHEN COALESCE(a.cycle_row_count,0)>0 THEN 1 ELSE 0 END AS cycle_flag,
         CASE WHEN COALESCE(a.maximum_depth,0)>=100 THEN 1 ELSE 0 END AS depth_limit_flag,
         CASE WHEN COALESCE(a.noncycle_path_count,0)>1 THEN 1 ELSE 0 END AS duplicate_path_flag
  FROM worker_snapshot AS w LEFT JOIN anchor_a_rollup AS a ON a.employee_id=w.employee_id
  CROSS JOIN anchor_b_reference AS b
),
voluntary_events AS (
  SELECT CAST(employee_id AS VARCHAR(64)) AS employee_id, CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type='Employee' AND employee_type='Regular' AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), ''))='VOLUNTARY' AND term_date IS NOT NULL
  GROUP BY 1,2
),
target_flags AS (
  SELECT m.employee_id, m.source_row_count, m.manager_assignment_count, m.et_leader_value_count,
         m.cycle_flag, m.depth_limit_flag, m.duplicate_path_flag,
         CASE WHEN m.anchor_a_member_flag=1 AND m.anchor_b_member_flag=1 THEN 1 ELSE 0 END AS branch_overlap_flag,
         CASE WHEN m.anchor_a_member_flag=1 OR m.anchor_b_member_flag=1 THEN 'CTO' ELSE 'Corp Fxn & BU' END AS category,
         MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
  FROM mapped_snapshot AS m CROSS JOIN snapshot_choice AS s LEFT JOIN voluntary_events AS v
    ON v.employee_id=m.employee_id AND v.term_date>s.snapshot_date AND v.term_date<=DATEADD(month,6,s.snapshot_date)
  GROUP BY 1,2,3,4,5,6,7,8,9
),
category_metrics AS (
  SELECT category, COUNT(*) AS employee_snapshot_count, COUNT(DISTINCT employee_id) AS distinct_employee_count,
         SUM(voluntary_attrition_target) AS voluntary_exits,
         100.0*SUM(voluntary_attrition_target)/NULLIF(COUNT(*),0) AS attrition_rate_percent
  FROM target_flags GROUP BY 1
),
metrics AS (
  SELECT 'duplicate_source_employee_count' AS metric, CAST(SUM(CASE WHEN source_row_count>1 THEN 1 ELSE 0 END) AS DECIMAL(18,8)) AS metric_value FROM target_flags
  UNION ALL SELECT 'manager_conflict_employee_count', CAST(SUM(CASE WHEN manager_assignment_count>1 THEN 1 ELSE 0 END) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'et_leader_conflict_employee_count', CAST(SUM(CASE WHEN et_leader_value_count>1 THEN 1 ELSE 0 END) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'anchor_a_cycle_count', CAST(SUM(cycle_flag) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'anchor_a_depth_limit_count', CAST(SUM(depth_limit_flag) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'anchor_a_duplicate_path_count', CAST(SUM(duplicate_path_flag) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'branch_overlap_count', CAST(SUM(branch_overlap_flag) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'anchor_b_reference_value_count', CAST(anchor_b_et_leader_value_count AS DECIMAL(18,8)) FROM anchor_b_reference
  UNION ALL SELECT 'anchor_b_reference_missing_flag', CAST(CASE WHEN anchor_b_et_leader IS NULL THEN 1 ELSE 0 END AS DECIMAL(18,8)) FROM anchor_b_reference
  UNION ALL SELECT 'category_reconciliation_difference', CAST((SELECT COUNT(*) FROM target_flags)-(SELECT SUM(employee_snapshot_count) FROM category_metrics) AS DECIMAL(18,8))
  UNION ALL SELECT 'category_below_minimum_count', CAST(COUNT(*) AS DECIMAL(18,8)) FROM category_metrics WHERE employee_snapshot_count<30 OR distinct_employee_count<30
)
SELECT s.snapshot_date, CAST('category' AS VARCHAR(16)) AS result_type, CAST(NULL AS VARCHAR(96)) AS metric, c.category,
       CAST(c.distinct_employee_count AS BIGINT) AS distinct_employee_count, CAST(c.employee_snapshot_count AS BIGINT) AS employee_snapshot_count,
       CAST(c.voluntary_exits AS BIGINT) AS voluntary_exits, CAST(ROUND(c.attrition_rate_percent,4) AS DECIMAL(18,4)) AS attrition_rate_percent,
       CAST(NULL AS DECIMAL(18,8)) AS metric_value
FROM category_metrics AS c CROSS JOIN snapshot_choice AS s
UNION ALL
SELECT s.snapshot_date, CAST('metric' AS VARCHAR(16)), metric, CAST(NULL AS VARCHAR(64)), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), metric_value
FROM metrics CROSS JOIN snapshot_choice AS s
ORDER BY result_type, metric, category;
