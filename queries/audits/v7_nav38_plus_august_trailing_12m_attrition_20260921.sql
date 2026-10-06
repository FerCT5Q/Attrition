/*
  Slides 38+ | fixed August baseline | aggregate-only evidence.

  Population: active Regular Employees, excluding RF360, at the 2025-08-24
  monthly snapshot.  The same employee cohort is followed for strict
  Voluntary terminations in (2025-08-24, 2026-08-23].

  This query intentionally keeps manager/team features at employee-snapshot
  grain for the attrition denominator.  The visible manager distributions
  may count managers, but their labels describe the attrition of the baseline
  direct reports assigned to each category.

  Acceptance rule:
    - one reconciled baseline row per employee;
    - no conflicting manager or category inputs among retained rows;
    - every displayed bucket has at least 30 baseline employees;
    - rate = distinct baseline employees with a strict Voluntary exit in the
      follow-up window / baseline employees in the same category.
*/
WITH params AS (
  SELECT DATE '2025-08-24' AS baseline_date,
         DATE '2026-08-23' AS outcome_cutoff
),
baseline_raw AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    MAX(CAST(w.manager_employee_id AS BIGINT)) AS manager_employee_id,
    MAX(NULLIF(TRIM(CAST(w.office_site AS VARCHAR(256))), '')) AS office_site,
    MAX(NULLIF(TRIM(CAST(w.city AS VARCHAR(256))), '')) AS city,
    MAX(COALESCE(w.manager_change, 0)) AS manager_change,
    MAX(COALESCE(w.is_transferred, 0)) AS is_transferred,
    MAX(COALESCE(w.location_change, 0)) AS location_change,
    MAX(COALESCE(w.job_family_change, 0)) AS job_family_change,
    MAX(COALESCE(w.cost_center_change, 0)) AS cost_center_change,
    MAX(COALESCE(w.is_promo, 0)) AS is_promo,
    MAX(CASE WHEN NULLIF(TRIM(CAST(w.et_1_leader AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END) AS et_1_present,
    MAX(CASE WHEN NULLIF(TRIM(CAST(w.et_2_leader AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END) AS et_2_present,
    MAX(CASE WHEN NULLIF(TRIM(CAST(w.et_3_leader AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END) AS et_3_present,
    MAX(CASE WHEN NULLIF(TRIM(CAST(w.et_4_leader AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END) AS et_4_present,
    MAX(CASE WHEN NULLIF(TRIM(CAST(w.et_5_leader AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END) AS et_5_present,
    MAX(CASE WHEN NULLIF(TRIM(CAST(w.et_6_leader AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END) AS et_6_present,
    MAX(CASE WHEN NULLIF(TRIM(CAST(w.et_7_leader AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END) AS et_7_present,
    MAX(CASE WHEN NULLIF(TRIM(CAST(w.et_8_leader AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END) AS et_8_present,
    MAX(CASE WHEN NULLIF(TRIM(CAST(w.et_9_leader AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END) AS et_9_present,
    MAX(CASE WHEN NULLIF(TRIM(CAST(w.et_10_leader AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END) AS et_10_present,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT COALESCE(CAST(w.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_variants,
    COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.office_site AS VARCHAR(256))), ''), '<NULL>')) AS office_site_variants
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_date
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND COALESCE(w.is_rf360_yes_no, 0) = 0
    AND w.employee_id IS NOT NULL
  GROUP BY 1
),
baseline AS (
  SELECT b.employee_id, b.manager_employee_id, b.office_site, b.city,
         b.manager_change, b.is_transferred, b.location_change,
         b.job_family_change, b.cost_center_change, b.is_promo,
         b.et_1_present, b.et_2_present, b.et_3_present, b.et_4_present,
         b.et_5_present, b.et_6_present, b.et_7_present, b.et_8_present,
         b.et_9_present, b.et_10_present, b.source_rows,
         b.manager_variants, b.office_site_variants,
         CASE WHEN et_1_present + et_2_present + et_3_present + et_4_present
                    + et_5_present + et_6_present + et_7_present + et_8_present
                    + et_9_present + et_10_present = 0 THEN '0'
              WHEN et_1_present + et_2_present + et_3_present + et_4_present
                    + et_5_present + et_6_present + et_7_present + et_8_present
                    + et_9_present + et_10_present = 1 THEN '1'
              WHEN et_1_present + et_2_present + et_3_present + et_4_present
                    + et_5_present + et_6_present + et_7_present + et_8_present
                    + et_9_present + et_10_present = 2 THEN '2'
              ELSE '3+' END AS et_count_category,
         CASE WHEN manager_change = 1 OR is_transferred = 1 OR location_change = 1
                   OR job_family_change = 1 OR cost_center_change = 1
              THEN '1+ proxy movement' ELSE 'No proxy movement' END AS major_inflection_proxy
  FROM baseline_raw b
),
manager_snapshot AS (
  SELECT employee_id AS manager_employee_id,
         MAX(NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), '')) AS manager_office_site,
         COUNT(*) AS source_rows,
         COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), ''), '<NULL>')) AS office_site_variants
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_date
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND COALESCE(w.is_rf360_yes_no, 0) = 0
    AND w.employee_id IS NOT NULL
  GROUP BY 1
),
office_categorized AS (
  SELECT b.employee_id,
         CASE
           WHEN b.manager_employee_id IS NULL OR m.manager_employee_id IS NULL
             OR b.office_site IS NULL OR m.manager_office_site IS NULL
             OR b.manager_variants <> 1 OR b.office_site_variants <> 1
             OR m.office_site_variants <> 1
           THEN 'Not comparable / missing site'
           WHEN UPPER(b.office_site) = UPPER(m.manager_office_site) THEN 'Same office_site'
           ELSE 'Different office_site'
         END AS category
  FROM baseline b
  LEFT JOIN manager_snapshot m ON m.manager_employee_id = b.manager_employee_id
),
voluntary_events AS (
  SELECT CAST(w.employee_id AS BIGINT) AS employee_id,
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
targets AS (
  SELECT b.employee_id,
         CASE WHEN v.employee_id IS NULL THEN 0 ELSE 1 END AS voluntary_attrition_target
  FROM baseline b
  LEFT JOIN (SELECT DISTINCT employee_id FROM voluntary_events) v
    ON v.employee_id = b.employee_id
),
manager_change_events AS (
  SELECT CAST(w.employee_id AS BIGINT) AS employee_id,
         CAST(w.manager_change_date AS DATE) AS event_date,
         MAX(COALESCE(w.manager_change, 0)) AS positive_manager_change,
         MAX(COALESCE(w.is_transferred, 0)) AS positive_transfer,
         MAX(COALESCE(w.is_promo, 0)) AS positive_promotion,
         MIN(CAST(w.fis_mo_end_dt AS DATE)) AS first_observed_snapshot
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.employee_id IS NOT NULL
    AND w.manager_change_date IS NOT NULL
    AND CAST(w.manager_change_date AS DATE) > DATEADD(month, -12, p.baseline_date)
    AND CAST(w.manager_change_date AS DATE) <= p.baseline_date
  GROUP BY 1, 2
),
manager_event_counts AS (
  SELECT b.employee_id,
         COUNT(DISTINCT CASE WHEN e.positive_manager_change = 1
                              AND e.event_date > DATEADD(month, -6, p.baseline_date)
                             THEN e.event_date END) AS count_6m,
         COUNT(DISTINCT CASE WHEN e.positive_manager_change = 1 THEN e.event_date END) AS count_12m,
         COUNT(DISTINCT CASE WHEN e.positive_manager_change = 1
                              AND e.positive_transfer = 0 AND e.positive_promotion = 0
                              AND e.event_date > DATEADD(month, -6, p.baseline_date)
                             THEN e.event_date END) AS sensitivity_count_6m,
         COUNT(DISTINCT CASE WHEN e.positive_manager_change = 1
                              AND e.positive_transfer = 0 AND e.positive_promotion = 0
                             THEN e.event_date END) AS sensitivity_count_12m
  FROM baseline b
  CROSS JOIN params p
  LEFT JOIN manager_change_events e ON e.employee_id = b.employee_id
  GROUP BY 1
),
manager_change_categories AS (
  SELECT employee_id, CAST('All observed manager changes · trailing 6 months' AS VARCHAR(256)) AS metric,
         CASE WHEN count_6m >= 3 THEN '3+' ELSE CAST(count_6m AS VARCHAR(8)) END AS category FROM manager_event_counts
  UNION ALL SELECT employee_id, CAST('All observed manager changes · trailing 12 months' AS VARCHAR(256)), CASE WHEN count_12m >= 3 THEN '3+' ELSE CAST(count_12m AS VARCHAR(8)) END FROM manager_event_counts
  UNION ALL SELECT employee_id, CAST('Sensitivity: exclude same-date transfer/promotion · trailing 6 months' AS VARCHAR(256)), CASE WHEN sensitivity_count_6m >= 3 THEN '3+' ELSE CAST(sensitivity_count_6m AS VARCHAR(8)) END FROM manager_event_counts
  UNION ALL SELECT employee_id, CAST('Sensitivity: exclude same-date transfer/promotion · trailing 12 months' AS VARCHAR(256)), CASE WHEN sensitivity_count_12m >= 3 THEN '3+' ELSE CAST(sensitivity_count_12m AS VARCHAR(8)) END FROM manager_event_counts
),
baseline_manager_exits AS (
  SELECT DISTINCT CAST(a.employeeid AS BIGINT) AS manager_employee_id,
         CAST(a.term_date AS DATE) AS term_date
  FROM hrda.all_terminations a
  CROSS JOIN params p
  WHERE UPPER(NULLIF(TRIM(CAST(a.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND CAST(a.term_date AS DATE) > DATEADD(month, -6, p.baseline_date)
    AND CAST(a.term_date AS DATE) <= p.baseline_date
    AND a.employeeid IS NOT NULL
),
manager_leaving_categories AS (
  SELECT b.employee_id,
         CASE WHEN e.manager_employee_id IS NULL THEN 'Not exposed' ELSE 'Exposed (1+)' END AS category
  FROM baseline b
  LEFT JOIN (SELECT DISTINCT manager_employee_id FROM baseline_manager_exits) e
    ON e.manager_employee_id = b.manager_employee_id
),
prior_employee_manager_rows AS (
  SELECT CAST(w.employee_id AS BIGINT) AS employee_id,
         CAST(w.manager_employee_id AS BIGINT) AS manager_employee_id,
         CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
         ROW_NUMBER() OVER (PARTITION BY w.employee_id, CAST(w.fis_mo_end_dt AS DATE)
                            ORDER BY CAST(w.manager_employee_id AS BIGINT)) AS row_rank
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
    AND w.manager_employee_id IS NOT NULL
    AND CAST(w.fis_mo_end_dt AS DATE) > DATEADD(month, -6, p.baseline_date)
    AND CAST(w.fis_mo_end_dt AS DATE) <= p.baseline_date
),
prior_employee_manager AS (
  SELECT employee_id, manager_employee_id, snapshot_date
  FROM prior_employee_manager_rows WHERE row_rank = 1
),
prior_voluntary_events AS (
  SELECT CAST(w.employee_id AS BIGINT) AS employee_id,
         CAST(w.term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > DATEADD(month, -6, p.baseline_date)
    AND CAST(w.term_date AS DATE) <= p.baseline_date
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2
),
team_exit_attribution AS (
  SELECT e.employee_id, e.term_date, h.manager_employee_id,
         ROW_NUMBER() OVER (PARTITION BY e.employee_id, e.term_date ORDER BY h.snapshot_date DESC) AS row_rank
  FROM prior_voluntary_events e
  INNER JOIN prior_employee_manager h
    ON h.employee_id = e.employee_id
   AND h.snapshot_date < e.term_date
   AND h.snapshot_date >= DATEADD(day, -45, e.term_date)
  WHERE e.employee_id <> h.manager_employee_id
),
team_manager_history AS (
  SELECT DISTINCT manager_employee_id FROM prior_employee_manager
),
team_exit_counts AS (
  SELECT manager_employee_id, COUNT(DISTINCT employee_id || ':' || CAST(term_date AS VARCHAR(32))) AS team_exit_count
  FROM team_exit_attribution WHERE row_rank = 1 GROUP BY 1
),
team_exit_categories AS (
  SELECT b.employee_id,
         CASE WHEN h.manager_employee_id IS NULL THEN 'Unknown'
              WHEN COALESCE(t.team_exit_count, 0) = 0 THEN '0'
              WHEN t.team_exit_count = 1 THEN '1'
              ELSE '2+' END AS category
  FROM baseline b
  LEFT JOIN team_manager_history h ON h.manager_employee_id = b.manager_employee_id
  LEFT JOIN team_exit_counts t ON t.manager_employee_id = b.manager_employee_id
),
category_rows AS (
  SELECT CAST('office_site_relationship' AS VARCHAR(256)) AS metric, CAST(c.category AS VARCHAR(256)) AS category, c.employee_id, t.voluntary_attrition_target FROM office_categorized c INNER JOIN targets t USING (employee_id)
  UNION ALL SELECT 'manager_change', CASE WHEN b.manager_change = 1 THEN 'Manager change (1)' ELSE 'No manager change (0)' END, b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id)
  UNION ALL SELECT 'manager_leaving_baseline_6m', c.category, c.employee_id, t.voluntary_attrition_target FROM manager_leaving_categories c INNER JOIN targets t USING (employee_id)
  UNION ALL SELECT 'recent_team_exits_under_manager', c.category, c.employee_id, t.voluntary_attrition_target FROM team_exit_categories c INNER JOIN targets t USING (employee_id)
  UNION ALL SELECT 'major_inflection_proxy', b.major_inflection_proxy, b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id)
  UNION ALL SELECT 'et_populated_field_count', b.et_count_category, b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id)
  UNION ALL SELECT 'et_field_presence', 'et_1', b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id) WHERE b.et_1_present = 1
  UNION ALL SELECT 'et_field_presence', 'et_2', b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id) WHERE b.et_2_present = 1
  UNION ALL SELECT 'et_field_presence', 'et_3', b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id) WHERE b.et_3_present = 1
  UNION ALL SELECT 'et_field_presence', 'et_4', b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id) WHERE b.et_4_present = 1
  UNION ALL SELECT 'et_field_presence', 'et_5', b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id) WHERE b.et_5_present = 1
  UNION ALL SELECT 'et_field_presence', 'et_6', b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id) WHERE b.et_6_present = 1
  UNION ALL SELECT 'et_field_presence', 'et_7', b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id) WHERE b.et_7_present = 1
  UNION ALL SELECT 'et_field_presence', 'et_8', b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id) WHERE b.et_8_present = 1
  UNION ALL SELECT 'et_field_presence', 'et_9', b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id) WHERE b.et_9_present = 1
  UNION ALL SELECT 'et_field_presence', 'et_10', b.employee_id, t.voluntary_attrition_target FROM baseline b INNER JOIN targets t USING (employee_id) WHERE b.et_10_present = 1
  UNION ALL SELECT c.metric, c.category, c.employee_id, t.voluntary_attrition_target FROM manager_change_categories c INNER JOIN targets t USING (employee_id)
),
category_metrics AS (
  SELECT metric, category,
         COUNT(DISTINCT employee_id) AS employee_count,
         COUNT(DISTINCT CASE WHEN voluntary_attrition_target = 1 THEN employee_id END) AS voluntary_exits,
         ROUND(100.0 * COUNT(DISTINCT CASE WHEN voluntary_attrition_target = 1 THEN employee_id END) / NULLIF(COUNT(DISTINCT employee_id), 0), 4) AS annual_attrition_rate_percent
  FROM category_rows GROUP BY 1, 2
),
diagnostics AS (
  SELECT COUNT(*) AS baseline_employee_count,
         SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
         SUM(CASE WHEN manager_variants > 1 OR office_site_variants > 1 THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count,
         (SELECT COUNT(DISTINCT employee_id) FROM voluntary_events) AS baseline_cohort_voluntary_exit_count
  FROM baseline
)
SELECT 'category' AS row_type, metric, category, employee_count, voluntary_exits,
       annual_attrition_rate_percent, CAST(NULL AS VARCHAR(64)) AS diagnostic_metric,
       CAST(NULL AS BIGINT) AS diagnostic_value,
       CASE WHEN employee_count >= 30 THEN 'publishable' ELSE 'not_estimable_below_30_baseline_employees' END AS publication_status
FROM category_metrics
UNION ALL
SELECT 'diagnostic', NULL, NULL, NULL, NULL, NULL, 'baseline_employee_count', baseline_employee_count, NULL FROM diagnostics
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, NULL, 'duplicate_employee_snapshot_count', duplicate_employee_snapshot_count, NULL FROM diagnostics
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, NULL, 'conflicting_employee_snapshot_count', conflicting_employee_snapshot_count, NULL FROM diagnostics
UNION ALL SELECT 'diagnostic', NULL, NULL, NULL, NULL, NULL, 'baseline_cohort_voluntary_exit_count', baseline_cohort_voluntary_exit_count, NULL FROM diagnostics
ORDER BY row_type, metric, category, diagnostic_metric;
