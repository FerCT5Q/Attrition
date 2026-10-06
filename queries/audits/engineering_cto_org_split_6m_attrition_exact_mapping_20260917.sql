/*
  Attrition V7 -- CTO versus Corp Fxn & BU six-month attrition audit.

  Claim: The documented CTO split can be assigned using only the prediction
  snapshot and compared on subsequent six-month VOLUNTARY attrition.

  Population: active Regular Employees (worker_type='Employee',
  employee_type='Regular', active_status=1), no RF360 filter. This matches
  the lower CTO display universe. Grain: distinct employee-snapshot.

  Window: the latest 24 monthly snapshots with complete six-month follow-up.
  Target: a strictly VOLUNTARY term_date in (snapshot_date, snapshot_date +
  6 months]. Voluntary Exception and all non-voluntary/ambiguous terms are
  excluded.

  Documented mapping: CTO is the union of (a) active same-snapshot descendants
  of documented anchor A (employee_id 892, including the anchor if active),
  and (b) documented anchor B (employee_id 1200) plus the employees whose
  et_leader equals the one constant normalized value recorded for anchor B.
  Corp Fxn & BU is the complement. Anchor IDs and et_leader values never leave
  this query.

  Acceptance rule, stated before execution:
  - 24 completed cohorts; the two categories reconcile to every eligible row;
  - zero source duplicates, manager/et_leader conflicts, branch overlap, or
    duplicate anchor-A paths;
  - anchor B has exactly one normalized et_leader reference value;
  - the reconstructed anchor-A branch has no member at depth 13, proving the
    explicit same-snapshot expansion through depth 12 is complete;
  - both categories have >=30 distinct employees and employee-snapshot
    exposures.
*/
WITH
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
    CASE WHEN manager_assignment_count = 1 THEN canonical_manager_employee_id END AS manager_employee_id,
    et_leader_value_count,
    CASE WHEN et_leader_value_count = 1 THEN canonical_et_leader END AS et_leader
  FROM employee_rollup
),
anchor_a_depth_1 AS (
  SELECT snapshot_date, employee_id
  FROM worker_snapshot
  WHERE manager_employee_id = '892'
),
anchor_a_depth_2 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_1 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_3 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_2 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_4 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_3 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_5 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_4 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_6 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_5 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_7 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_6 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_8 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_7 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_9 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_8 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_10 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_9 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_11 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_10 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_12 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_11 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_depth_13 AS (
  SELECT w.snapshot_date, w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN anchor_a_depth_12 AS p
    ON p.snapshot_date = w.snapshot_date AND p.employee_id = w.manager_employee_id
),
anchor_a_members_raw AS (
  SELECT snapshot_date, employee_id, 0 AS member_depth FROM worker_snapshot WHERE employee_id = '892'
  UNION ALL SELECT snapshot_date, employee_id, 1 FROM anchor_a_depth_1
  UNION ALL SELECT snapshot_date, employee_id, 2 FROM anchor_a_depth_2
  UNION ALL SELECT snapshot_date, employee_id, 3 FROM anchor_a_depth_3
  UNION ALL SELECT snapshot_date, employee_id, 4 FROM anchor_a_depth_4
  UNION ALL SELECT snapshot_date, employee_id, 5 FROM anchor_a_depth_5
  UNION ALL SELECT snapshot_date, employee_id, 6 FROM anchor_a_depth_6
  UNION ALL SELECT snapshot_date, employee_id, 7 FROM anchor_a_depth_7
  UNION ALL SELECT snapshot_date, employee_id, 8 FROM anchor_a_depth_8
  UNION ALL SELECT snapshot_date, employee_id, 9 FROM anchor_a_depth_9
  UNION ALL SELECT snapshot_date, employee_id, 10 FROM anchor_a_depth_10
  UNION ALL SELECT snapshot_date, employee_id, 11 FROM anchor_a_depth_11
  UNION ALL SELECT snapshot_date, employee_id, 12 FROM anchor_a_depth_12
),
anchor_a_member_rollup AS (
  SELECT
    snapshot_date,
    employee_id,
    MIN(member_depth) AS minimum_member_depth,
    COUNT(*) AS membership_path_count
  FROM anchor_a_members_raw
  GROUP BY 1, 2
),
anchor_b_reference AS (
  SELECT
    MIN(NULLIF(TRIM(CAST(et_leader AS VARCHAR(256))), '')) AS anchor_b_et_leader,
    COUNT(DISTINCT NULLIF(TRIM(CAST(et_leader AS VARCHAR(256))), '')) AS anchor_b_et_leader_value_count
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(employee_id AS VARCHAR(64)) = '1200'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
),
classified_snapshot AS (
  SELECT
    w.snapshot_date,
    w.employee_id,
    w.source_row_count,
    w.manager_assignment_count,
    w.et_leader_value_count,
    CASE WHEN a.employee_id IS NOT NULL THEN 1 ELSE 0 END AS anchor_a_member_flag,
    CASE
      WHEN w.employee_id = '1200' THEN 1
      WHEN b.anchor_b_et_leader IS NOT NULL
       AND UPPER(TRIM(w.et_leader)) = UPPER(TRIM(b.anchor_b_et_leader)) THEN 1
      ELSE 0
    END AS anchor_b_member_flag,
    COALESCE(a.membership_path_count, 0) AS anchor_a_membership_path_count
  FROM worker_snapshot AS w
  LEFT JOIN anchor_a_member_rollup AS a
    ON a.snapshot_date = w.snapshot_date AND a.employee_id = w.employee_id
  CROSS JOIN anchor_b_reference AS b
),
mapped_snapshot AS (
  SELECT
    snapshot_date,
    employee_id,
    source_row_count,
    manager_assignment_count,
    et_leader_value_count,
    anchor_a_membership_path_count,
    CASE WHEN anchor_a_member_flag = 1 AND anchor_b_member_flag = 1 THEN 1 ELSE 0 END AS branch_overlap_flag,
    CASE WHEN anchor_a_member_flag = 1 OR anchor_b_member_flag = 1 THEN 'CTO' ELSE 'Corp Fxn & BU' END AS category
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
    s.anchor_a_membership_path_count,
    s.branch_overlap_flag,
    MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
  FROM mapped_snapshot AS s
  LEFT JOIN voluntary_events AS v
    ON v.employee_id = s.employee_id
   AND v.term_date > s.snapshot_date
   AND v.term_date <= DATEADD(month, 6, s.snapshot_date)
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
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
  SELECT 'completed_snapshot_count' AS metric, CAST((SELECT COUNT(*) FROM eligible_snapshot_dates) AS DECIMAL(18, 8)) AS metric_value
  UNION ALL SELECT 'eligible_employee_snapshot_count', CAST(COUNT(*) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT 'duplicate_source_employee_snapshot_count', CAST(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT 'manager_conflict_employee_snapshot_count', CAST(SUM(CASE WHEN manager_assignment_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT 'et_leader_conflict_employee_snapshot_count', CAST(SUM(CASE WHEN et_leader_value_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT 'anchor_a_duplicate_member_employee_snapshot_count', CAST(SUM(CASE WHEN anchor_a_membership_path_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT 'anchor_a_depth_13_employee_snapshot_count', CAST(COUNT(*) AS DECIMAL(18, 8)) FROM anchor_a_depth_13
  UNION ALL SELECT 'anchor_a_direct_report_employee_snapshot_count', CAST(COUNT(*) AS DECIMAL(18, 8)) FROM anchor_a_depth_1
  UNION ALL SELECT 'branch_overlap_employee_snapshot_count', CAST(SUM(branch_overlap_flag) AS DECIMAL(18, 8)) FROM target_flags
  UNION ALL SELECT 'anchor_b_reference_distinct_et_leader_value_count', CAST(anchor_b_et_leader_value_count AS DECIMAL(18, 8)) FROM anchor_b_reference
  UNION ALL SELECT 'anchor_b_reference_missing_flag', CAST(CASE WHEN anchor_b_et_leader IS NULL THEN 1 ELSE 0 END AS DECIMAL(18, 8)) FROM anchor_b_reference
  UNION ALL SELECT 'category_reconciliation_difference', CAST((SELECT COUNT(*) FROM target_flags) - (SELECT SUM(employee_snapshot_count) FROM category_metrics) AS DECIMAL(18, 8))
  UNION ALL SELECT 'categories_below_minimum_employee_exposure', CAST(COUNT(*) AS DECIMAL(18, 8)) FROM category_metrics WHERE employee_snapshot_count < 30 OR distinct_employee_count < 30
  UNION ALL SELECT 'minimum_category_employee_snapshot_count', CAST(MIN(employee_snapshot_count) AS DECIMAL(18, 8)) FROM category_metrics
  UNION ALL SELECT 'minimum_category_distinct_employee_count', CAST(MIN(distinct_employee_count) AS DECIMAL(18, 8)) FROM category_metrics
  UNION ALL SELECT 'category_count', CAST(COUNT(*) AS DECIMAL(18, 8)) FROM category_metrics
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
