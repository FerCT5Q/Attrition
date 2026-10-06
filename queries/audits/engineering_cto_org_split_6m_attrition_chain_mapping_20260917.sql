/*
  CTO vs. Corp Fxn & BU -- six-month voluntary attrition, V7.

  Exact same-snapshot mapping used by the organizational display:
  CTO = documented anchor A (892) and active descendants reached through
  manager_employee_id, plus documented anchor B (1200) and the single
  normalized et_leader value attached to anchor B. Corp Fxn & BU is the
  complement. IDs and et_leader values remain inside this aggregate-only SQL.

  Population: active Regular Employees; no RF360 filter. Outcome: at least one
  term_type='VOLUNTARY' in (snapshot_date, snapshot_date + 6 months].
  Window: latest 24 monthly snapshots with complete follow-up.

  Acceptance rule: 24 cohorts, zero duplicate source rows / manager or
  et_leader conflicts / chain cycles / chain depth beyond 13 / branch overlap,
  one anchor-B reference value, category reconciliation, and n>=30 per group.
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
    SELECT CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
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
  SELECT d.snapshot_date,
         CAST(w.employee_id AS VARCHAR(64)) AS employee_id,
         NULLIF(TRIM(CAST(w.manager_employee_id AS VARCHAR(64))), '') AS manager_employee_id,
         NULLIF(TRIM(CAST(w.et_leader AS VARCHAR(256))), '') AS et_leader
  FROM hrda.post_hire_monthly_worker_dtls AS w
  INNER JOIN eligible_snapshot_dates AS d ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
  WHERE w.worker_type = 'Employee' AND w.employee_type = 'Regular'
    AND w.active_status = 1 AND w.employee_id IS NOT NULL
),
employee_rollup AS (
  SELECT snapshot_date, employee_id,
         COUNT(*) AS source_row_count,
         COUNT(DISTINCT COALESCE(manager_employee_id, '<NULL>')) AS manager_assignment_count,
         MIN(manager_employee_id) AS canonical_manager_employee_id,
         COUNT(DISTINCT COALESCE(et_leader, '<NULL>')) AS et_leader_value_count,
         MIN(et_leader) AS canonical_et_leader
  FROM raw_snapshot
  GROUP BY 1, 2
),
worker_snapshot AS (
  SELECT snapshot_date, employee_id, source_row_count, manager_assignment_count,
         CASE WHEN manager_assignment_count = 1 THEN canonical_manager_employee_id END AS manager_employee_id,
         et_leader_value_count,
         CASE WHEN et_leader_value_count = 1 THEN canonical_et_leader END AS et_leader
  FROM employee_rollup
),
chain_1 AS (
  SELECT w.snapshot_date, w.employee_id,
         m.employee_id AS manager_1_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM worker_snapshot AS w
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = w.snapshot_date AND m.employee_id = w.manager_employee_id
),
chain_2 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id,
         m.employee_id AS manager_2_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_1 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_3 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id,
         m.employee_id AS manager_3_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_2 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_4 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id,
         m.employee_id AS manager_4_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_3 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_5 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id,
         m.employee_id AS manager_5_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_4 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_6 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id,
         m.employee_id AS manager_6_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_5 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_7 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id,
         m.employee_id AS manager_7_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_6 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_8 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id,
         m.employee_id AS manager_8_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_7 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_9 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id, c.manager_8_employee_id,
         m.employee_id AS manager_9_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_8 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_10 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id, c.manager_8_employee_id, c.manager_9_employee_id,
         m.employee_id AS manager_10_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_9 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_11 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id, c.manager_8_employee_id, c.manager_9_employee_id, c.manager_10_employee_id,
         m.employee_id AS manager_11_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_10 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_12 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id, c.manager_8_employee_id, c.manager_9_employee_id, c.manager_10_employee_id, c.manager_11_employee_id,
         m.employee_id AS manager_12_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_11 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
chain_13 AS (
  SELECT c.snapshot_date, c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id, c.manager_8_employee_id, c.manager_9_employee_id, c.manager_10_employee_id, c.manager_11_employee_id, c.manager_12_employee_id,
         m.employee_id AS manager_13_employee_id,
         m.manager_employee_id AS next_manager_employee_id
  FROM chain_12 AS c
  LEFT JOIN worker_snapshot AS m ON m.snapshot_date = c.snapshot_date AND m.employee_id = c.next_manager_employee_id
),
anchor_b_reference AS (
  SELECT MIN(NULLIF(TRIM(CAST(et_leader AS VARCHAR(256))), '')) AS anchor_b_et_leader,
         COUNT(DISTINCT NULLIF(TRIM(CAST(et_leader AS VARCHAR(256))), '')) AS anchor_b_et_leader_value_count
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(employee_id AS VARCHAR(64)) = '1200'
    AND worker_type = 'Employee' AND employee_type = 'Regular'
),
mapped_snapshot AS (
  SELECT w.snapshot_date, w.employee_id, w.source_row_count,
         w.manager_assignment_count, w.et_leader_value_count,
         CASE WHEN c.next_manager_employee_id IS NOT NULL THEN 1 ELSE 0 END AS chain_depth_over_13_flag,
         CASE WHEN c.manager_1_employee_id = c.employee_id
                OR c.manager_2_employee_id IN (c.employee_id, c.manager_1_employee_id)
                OR c.manager_3_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id)
                OR c.manager_4_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id)
                OR c.manager_5_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id)
                OR c.manager_6_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id)
                OR c.manager_7_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id)
                OR c.manager_8_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id)
                OR c.manager_9_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id, c.manager_8_employee_id)
                OR c.manager_10_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id, c.manager_8_employee_id, c.manager_9_employee_id)
                OR c.manager_11_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id, c.manager_8_employee_id, c.manager_9_employee_id, c.manager_10_employee_id)
                OR c.manager_12_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id, c.manager_8_employee_id, c.manager_9_employee_id, c.manager_10_employee_id, c.manager_11_employee_id)
                OR c.manager_13_employee_id IN (c.employee_id, c.manager_1_employee_id, c.manager_2_employee_id, c.manager_3_employee_id, c.manager_4_employee_id, c.manager_5_employee_id, c.manager_6_employee_id, c.manager_7_employee_id, c.manager_8_employee_id, c.manager_9_employee_id, c.manager_10_employee_id, c.manager_11_employee_id, c.manager_12_employee_id)
              THEN 1 ELSE 0 END AS chain_cycle_flag,
         CASE WHEN c.employee_id = '892' OR c.manager_1_employee_id = '892' OR c.manager_2_employee_id = '892'
                OR c.manager_3_employee_id = '892' OR c.manager_4_employee_id = '892'
                OR c.manager_5_employee_id = '892' OR c.manager_6_employee_id = '892'
                OR c.manager_7_employee_id = '892' OR c.manager_8_employee_id = '892'
                OR c.manager_9_employee_id = '892' OR c.manager_10_employee_id = '892'
                OR c.manager_11_employee_id = '892' OR c.manager_12_employee_id = '892'
                OR c.manager_13_employee_id = '892'
              THEN 1 ELSE 0 END AS anchor_a_member_flag,
         CASE WHEN c.employee_id = '1200'
                   OR (b.anchor_b_et_leader IS NOT NULL AND UPPER(TRIM(w.et_leader)) = UPPER(TRIM(b.anchor_b_et_leader)))
              THEN 1 ELSE 0 END AS anchor_b_member_flag
  FROM chain_13 AS c
  INNER JOIN worker_snapshot AS w
    ON w.snapshot_date = c.snapshot_date AND w.employee_id = c.employee_id
  CROSS JOIN anchor_b_reference AS b
),
category_snapshot AS (
  SELECT snapshot_date, employee_id, source_row_count, manager_assignment_count,
         et_leader_value_count, chain_depth_over_13_flag, chain_cycle_flag,
         anchor_a_member_flag, anchor_b_member_flag,
         CASE WHEN anchor_a_member_flag = 1 AND anchor_b_member_flag = 1 THEN 1 ELSE 0 END AS branch_overlap_flag,
         CASE WHEN anchor_a_member_flag = 1 OR anchor_b_member_flag = 1 THEN 'CTO' ELSE 'Corp Fxn & BU' END AS category
  FROM mapped_snapshot
),
voluntary_events AS (
  SELECT CAST(employee_id AS VARCHAR(64)) AS employee_id, CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee' AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
  GROUP BY 1, 2
),
target_flags AS (
  SELECT s.snapshot_date, s.employee_id, s.category, s.source_row_count,
         s.manager_assignment_count, s.et_leader_value_count,
         s.chain_depth_over_13_flag, s.chain_cycle_flag, s.branch_overlap_flag,
         MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
  FROM category_snapshot AS s
  LEFT JOIN voluntary_events AS v ON v.employee_id = s.employee_id
    AND v.term_date > s.snapshot_date AND v.term_date <= DATEADD(month, 6, s.snapshot_date)
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
),
category_metrics AS (
  SELECT category, MIN(snapshot_date) AS first_snapshot_date, MAX(snapshot_date) AS last_snapshot_date,
         COUNT(DISTINCT employee_id) AS distinct_employee_count, COUNT(*) AS employee_snapshot_count,
         SUM(voluntary_attrition_target) AS voluntary_exits,
         100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0) AS attrition_rate_percent
  FROM target_flags GROUP BY 1
),
audit_metrics AS (
  SELECT 'completed_snapshot_count' AS metric, CAST((SELECT COUNT(*) FROM eligible_snapshot_dates) AS DECIMAL(18,8)) AS metric_value
  UNION ALL SELECT 'eligible_employee_snapshot_count', CAST(COUNT(*) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'duplicate_source_employee_snapshot_count', CAST(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'manager_conflict_employee_snapshot_count', CAST(SUM(CASE WHEN manager_assignment_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'et_leader_conflict_employee_snapshot_count', CAST(SUM(CASE WHEN et_leader_value_count > 1 THEN 1 ELSE 0 END) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'manager_chain_cycle_employee_snapshot_count', CAST(SUM(chain_cycle_flag) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'manager_chain_depth_over_13_employee_snapshot_count', CAST(SUM(chain_depth_over_13_flag) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'branch_overlap_employee_snapshot_count', CAST(SUM(branch_overlap_flag) AS DECIMAL(18,8)) FROM target_flags
  UNION ALL SELECT 'anchor_b_reference_distinct_et_leader_value_count', CAST(anchor_b_et_leader_value_count AS DECIMAL(18,8)) FROM anchor_b_reference
  UNION ALL SELECT 'anchor_b_reference_missing_flag', CAST(CASE WHEN anchor_b_et_leader IS NULL THEN 1 ELSE 0 END AS DECIMAL(18,8)) FROM anchor_b_reference
  UNION ALL SELECT 'category_reconciliation_difference', CAST((SELECT COUNT(*) FROM target_flags) - (SELECT SUM(employee_snapshot_count) FROM category_metrics) AS DECIMAL(18,8))
  UNION ALL SELECT 'categories_below_minimum_employee_exposure', CAST(COUNT(*) AS DECIMAL(18,8)) FROM category_metrics WHERE employee_snapshot_count < 30 OR distinct_employee_count < 30
  UNION ALL SELECT 'minimum_category_employee_snapshot_count', CAST(MIN(employee_snapshot_count) AS DECIMAL(18,8)) FROM category_metrics
  UNION ALL SELECT 'minimum_category_distinct_employee_count', CAST(MIN(distinct_employee_count) AS DECIMAL(18,8)) FROM category_metrics
  UNION ALL SELECT 'category_count', CAST(COUNT(*) AS DECIMAL(18,8)) FROM category_metrics
)
SELECT CAST('category' AS VARCHAR(16)) AS result_type, CAST(NULL AS VARCHAR(96)) AS metric,
       category, first_snapshot_date, last_snapshot_date,
       CAST(distinct_employee_count AS BIGINT) AS distinct_employee_count,
       CAST(employee_snapshot_count AS BIGINT) AS employee_snapshot_count,
       CAST(voluntary_exits AS BIGINT) AS voluntary_exits,
       CAST(ROUND(attrition_rate_percent, 4) AS DECIMAL(18,4)) AS attrition_rate_percent,
       CAST(NULL AS DECIMAL(18,8)) AS metric_value
FROM category_metrics
UNION ALL
SELECT CAST('metric' AS VARCHAR(16)), metric, CAST(NULL AS VARCHAR(64)), CAST(NULL AS DATE), CAST(NULL AS DATE),
       CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), metric_value
FROM audit_metrics
ORDER BY result_type, metric, category;
