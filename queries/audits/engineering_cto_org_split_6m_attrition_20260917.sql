/*
  Attrition V7 - CTO versus Corp Fxn & BU six-month attrition audit

  Claim tested
  ------------
  The documented organizational split can be assigned at each active regular
  employee snapshot and used to compare the subsequent six-month voluntary
  attrition rate without using future organization data.

  Semantic type: grouped_mapping with a same-snapshot hierarchy branch.
  Reporting mode: internal_analysis; aggregate results only.

  Population and target
  ---------------------
  - Active Regular Employees at the snapshot
      worker_type = 'Employee'; employee_type = 'Regular'; active_status = 1
  - Latest 24 monthly snapshots with a complete six-month outcome window.
  - Target: at least one strictly VOLUNTARY termination in
      (snapshot_date, snapshot_date + 6 months].
  - Corp Fxn & BU is the complement of CTO in each same-snapshot population.
  - No RF360 filter: this intentionally matches the lower organizational
    display universe, not the historic model feature population.

  Documented CTO mapping
  ----------------------
  - documented anchor A (employee_id 892) and its same-snapshot descendants,
    provided the audit confirms there are no active direct reports to that
    anchor in the 24 completed cohorts, or
  - documented anchor B (employee_id 1200) and employees whose same-snapshot
    et_leader equals anchor B's et_leader value.
  Anchor identifiers remain inside the query and never appear in results.

  Acceptance rule (defined before execution)
  -------------------------------------------
  1. Exactly 24 completed monthly cohorts are returned.
  2. Every active employee-snapshot maps once and only once to CTO or Corp
     Fxn & BU; category totals reconcile to the active snapshot population.
  3. No duplicate employee-snapshot source rows, manager conflicts, et_leader
     conflicts, or branch overlaps occur; anchor A has zero active direct
     reports in every cohort. With no direct report, that branch has no active
     descendants under the documented same-snapshot traversal rule.
  4. Both aggregate categories have at least 30 employee-snapshot exposures
     and 30 distinct employees.
  5. The outcome only counts term_type = 'VOLUNTARY' after the prediction
     snapshot and through the inclusive six-month boundary.
*/
WITH RECURSIVE
source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
),
eligible_snapshot_dates AS (
  SELECT snapshot_date
  FROM (
    SELECT
      CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
      ROW_NUMBER() OVER (ORDER BY CAST(w.fis_mo_end_dt AS DATE) DESC) AS recency_rank
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN source_bounds AS b
    WHERE w.fis_mo_end_dt IS NOT NULL
      AND CAST(w.fis_mo_end_dt AS DATE) <= DATEADD(month, -6, b.latest_snapshot_date)
    GROUP BY 1
  ) AS dated
  WHERE recency_rank <= 24
),
raw_snapshot AS (
  SELECT
    d.snapshot_date,
    CAST(w.employee_id AS VARCHAR(64)) AS employee_id,
    NULLIF(TRIM(CAST(w.manager_employee_id AS VARCHAR(64))), '') AS manager_employee_id,
    NULLIF(TRIM(CAST(w.et_leader AS VARCHAR(256))), '') AS et_leader
  FROM hrda.post_hire_monthly_worker_dtls AS w
  INNER JOIN eligible_snapshot_dates AS d
    ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
),
employee_rollup AS (
  SELECT
    snapshot_date,
    employee_id,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT COALESCE(manager_employee_id, '<NULL>')) AS manager_assignment_count,
    MIN(manager_employee_id) AS canonical_manager_employee_id,
    COUNT(DISTINCT COALESCE(et_leader, '<NULL>')) AS et_leader_value_count,
    MIN(et_leader) AS canonical_et_leader
  FROM raw_snapshot
  GROUP BY 1, 2
),
worker_snapshot AS (
  SELECT
    snapshot_date,
    employee_id,
    source_row_count,
    manager_assignment_count,
    CASE
      WHEN manager_assignment_count = 1 THEN canonical_manager_employee_id
      ELSE NULL
    END AS manager_employee_id,
    et_leader_value_count,
    CASE
      WHEN et_leader_value_count = 1 THEN canonical_et_leader
      ELSE NULL
    END AS et_leader
  FROM employee_rollup
),
anchor_a_snapshot_check AS (
  SELECT
    snapshot_date,
    SUM(CASE WHEN employee_id = '892' THEN 1 ELSE 0 END) AS anchor_a_active_count,
    SUM(CASE WHEN manager_employee_id = '892' THEN 1 ELSE 0 END) AS anchor_a_direct_report_count
  FROM worker_snapshot
  GROUP BY 1
),
anchor_b_values AS (
  SELECT
    w.snapshot_date,
    w.et_leader AS anchor_b_et_leader
  FROM worker_snapshot AS w
  WHERE w.employee_id = '1200'
),
classified_snapshot AS (
  SELECT
    w.snapshot_date,
    w.employee_id,
    w.source_row_count,
    w.manager_assignment_count,
    w.et_leader_value_count,
    CASE WHEN w.employee_id = '892' THEN 1 ELSE 0 END AS anchor_a_member_flag,
    CASE
      WHEN w.employee_id = '1200' THEN 1
      WHEN bv.anchor_b_et_leader IS NOT NULL
       AND UPPER(TRIM(w.et_leader)) = UPPER(TRIM(bv.anchor_b_et_leader)) THEN 1
      ELSE 0
    END AS anchor_b_member_flag,
    CAST(0 AS INTEGER) AS hierarchy_cycle_flag,
    CAST(0 AS INTEGER) AS hierarchy_depth_limit_flag,
    CAST(0 AS INTEGER) AS hierarchy_duplicate_path_flag,
    CASE WHEN bv.anchor_b_et_leader IS NULL THEN 1 ELSE 0 END AS anchor_b_et_leader_missing_flag,
    COALESCE(a.anchor_a_direct_report_count, 0) AS anchor_a_direct_report_count
  FROM worker_snapshot AS w
  LEFT JOIN anchor_a_snapshot_check AS a
    ON a.snapshot_date = w.snapshot_date
  LEFT JOIN anchor_b_values AS bv
    ON bv.snapshot_date = w.snapshot_date
),
mapped_snapshot AS (
  SELECT
    snapshot_date,
    employee_id,
    source_row_count,
    manager_assignment_count,
    et_leader_value_count,
    anchor_a_member_flag,
    anchor_b_member_flag,
    hierarchy_cycle_flag,
    hierarchy_depth_limit_flag,
    hierarchy_duplicate_path_flag,
    anchor_b_et_leader_missing_flag,
    anchor_a_direct_report_count,
    CASE
      WHEN anchor_a_member_flag = 1 AND anchor_b_member_flag = 1 THEN 1
      ELSE 0
    END AS branch_overlap_flag,
    CASE
      WHEN anchor_a_member_flag = 1 OR anchor_b_member_flag = 1 THEN 'CTO'
      ELSE 'Corp Fxn & BU'
    END AS category
  FROM classified_snapshot
),
voluntary_events AS (
  SELECT
    CAST(employee_id AS VARCHAR(64)) AS employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
  GROUP BY 1, 2
),
target_flags AS (
  SELECT
    s.snapshot_date,
    s.employee_id,
    s.category,
    s.source_row_count,
    s.manager_assignment_count,
    s.et_leader_value_count,
    s.hierarchy_cycle_flag,
    s.hierarchy_depth_limit_flag,
    s.hierarchy_duplicate_path_flag,
    s.anchor_b_et_leader_missing_flag,
    s.anchor_a_direct_report_count,
    s.branch_overlap_flag,
    MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
  FROM mapped_snapshot AS s
  LEFT JOIN voluntary_events AS v
    ON v.employee_id = s.employee_id
   AND v.term_date > s.snapshot_date
   AND v.term_date <= DATEADD(month, 6, s.snapshot_date)
  GROUP BY
    s.snapshot_date, s.employee_id, s.category, s.source_row_count,
    s.manager_assignment_count, s.et_leader_value_count,
    s.hierarchy_cycle_flag, s.hierarchy_depth_limit_flag,
    s.hierarchy_duplicate_path_flag, s.anchor_b_et_leader_missing_flag,
    s.anchor_a_direct_report_count,
    s.branch_overlap_flag
),
category_metrics AS (
  SELECT
    category,
    MIN(snapshot_date) AS first_snapshot_date,
    MAX(snapshot_date) AS last_snapshot_date,
    COUNT(DISTINCT employee_id) AS distinct_employee_count,
    COUNT(*) AS employee_snapshot_count,
    SUM(voluntary_attrition_target) AS voluntary_exits,
    100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0) AS attrition_rate_percent
  FROM target_flags
  GROUP BY 1
),
audit_metrics AS (
  SELECT
    'completed_snapshot_count' AS metric,
    CAST((SELECT COUNT(*) FROM eligible_snapshot_dates) AS DECIMAL(18, 8)) AS metric_value
  UNION ALL SELECT
    'eligible_employee_snapshot_count', CAST(COUNT(*) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'duplicate_source_employee_snapshot_count', CAST(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'manager_conflict_employee_snapshot_count', CAST(SUM(CASE WHEN manager_assignment_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'et_leader_conflict_employee_snapshot_count', CAST(SUM(CASE WHEN et_leader_value_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'hierarchy_cycle_employee_snapshot_count', CAST(SUM(hierarchy_cycle_flag) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'hierarchy_depth_limit_employee_snapshot_count', CAST(SUM(hierarchy_depth_limit_flag) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'hierarchy_duplicate_path_employee_snapshot_count', CAST(SUM(hierarchy_duplicate_path_flag) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'branch_overlap_employee_snapshot_count', CAST(SUM(branch_overlap_flag) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'anchor_b_et_leader_missing_snapshot_count', CAST(COUNT(DISTINCT CASE WHEN anchor_b_et_leader_missing_flag = 1 THEN snapshot_date END) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'anchor_a_direct_report_snapshot_count', CAST(COUNT(DISTINCT CASE WHEN anchor_a_direct_report_count > 0 THEN snapshot_date END) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'maximum_anchor_a_direct_report_count', CAST(MAX(anchor_a_direct_report_count) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT
    'category_reconciliation_difference', CAST(
      (SELECT COUNT(*) FROM target_flags) - (SELECT SUM(employee_snapshot_count) FROM category_metrics)
      AS DECIMAL(18, 8)
    )
  UNION ALL SELECT
    'categories_below_minimum_employee_exposure', CAST(COUNT(*) AS DECIMAL(18, 8))
  FROM category_metrics
  WHERE employee_snapshot_count < 30 OR distinct_employee_count < 30
  UNION ALL SELECT
    'minimum_category_employee_snapshot_count', CAST(MIN(employee_snapshot_count) AS DECIMAL(18, 8)) FROM category_metrics
  UNION ALL SELECT
    'minimum_category_distinct_employee_count', CAST(MIN(distinct_employee_count) AS DECIMAL(18, 8)) FROM category_metrics
  UNION ALL SELECT
    'category_count', CAST(COUNT(*) AS DECIMAL(18, 8)) FROM category_metrics
)
SELECT
  CAST('category' AS VARCHAR(16)) AS result_type,
  CAST(NULL AS VARCHAR(96)) AS metric,
  category,
  first_snapshot_date,
  last_snapshot_date,
  CAST(distinct_employee_count AS BIGINT) AS distinct_employee_count,
  CAST(employee_snapshot_count AS BIGINT) AS employee_snapshot_count,
  CAST(voluntary_exits AS BIGINT) AS voluntary_exits,
  CAST(ROUND(attrition_rate_percent, 4) AS DECIMAL(18, 4)) AS attrition_rate_percent,
  CAST(NULL AS DECIMAL(18, 8)) AS metric_value
FROM category_metrics

UNION ALL

SELECT
  CAST('metric' AS VARCHAR(16)) AS result_type,
  metric,
  CAST(NULL AS VARCHAR(64)) AS category,
  CAST(NULL AS DATE) AS first_snapshot_date,
  CAST(NULL AS DATE) AS last_snapshot_date,
  CAST(NULL AS BIGINT) AS distinct_employee_count,
  CAST(NULL AS BIGINT) AS employee_snapshot_count,
  CAST(NULL AS BIGINT) AS voluntary_exits,
  CAST(NULL AS DECIMAL(18, 4)) AS attrition_rate_percent,
  metric_value
FROM audit_metrics
ORDER BY result_type, metric, category;
