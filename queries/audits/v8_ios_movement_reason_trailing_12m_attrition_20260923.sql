/*
  V8 IOS movement reasons: trailing-12-month distribution plus annual
  voluntary attrition. Internal analysis, aggregate-only.

  Definition:
  - Current distribution: active Regular employees at 2026-08-23 with an IOS
    movement reason recorded in (2025-08-23, 2026-08-23].
  - Annual outcome label: same feature at 2025-08-24 using (2024-08-24,
    2025-08-24], then strict VOLUNTARY exits in (2025-08-24, 2026-08-23].
  - Reason rows can overlap. "All eligible IOS movements" is deduplicated by
    employee and is not the sum of the six reason rows.

  Employee IDs appear only inside joins, deduplication and COUNT(DISTINCT).
*/
WITH snapshots AS (
  SELECT 'baseline' AS snapshot_key, DATE '2025-08-24' AS snapshot_date
  UNION ALL
  SELECT 'current' AS snapshot_key, DATE '2026-08-23' AS snapshot_date
),
active_regular AS (
  SELECT
    s.snapshot_key,
    s.snapshot_date,
    w.employee_id
  FROM snapshots s
  JOIN hrda.post_hire_monthly_worker_dtls w
    ON w.fis_mo_end_dt::date = s.snapshot_date
   AND w.worker_type = 'Employee'
   AND w.employee_type = 'Regular'
   AND w.active_status = 1
  GROUP BY 1, 2, 3
),
population AS (
  SELECT snapshot_key, snapshot_date, COUNT(DISTINCT employee_id) AS active_regular_employees
  FROM active_regular
  GROUP BY 1, 2
),
raw_events AS (
  SELECT
    a.snapshot_key,
    a.snapshot_date,
    a.employee_id,
    t.effective_date::date AS effective_date,
    TRIM(t.business_process_reason) AS reason_value
  FROM active_regular a
  JOIN hrda.workers_ios_transfers t
    ON t.employee_id = a.employee_id
   AND t.effective_date::date > DATEADD(month, -12, a.snapshot_date)::date
   AND t.effective_date::date <= a.snapshot_date
  WHERE t.effective_date IS NOT NULL
    AND NULLIF(TRIM(t.business_process_reason), '') IS NOT NULL
),
eligible_events AS (
  SELECT snapshot_key, snapshot_date, employee_id, effective_date, reason_value
  FROM (
    SELECT
      snapshot_key,
      snapshot_date,
      employee_id,
      effective_date,
      reason_value,
      ROW_NUMBER() OVER (
        PARTITION BY snapshot_key, employee_id, effective_date, reason_value
        ORDER BY effective_date
      ) AS duplicate_rank
    FROM raw_events
  ) deduplicated
  WHERE duplicate_rank = 1
),
group_order AS (
  SELECT 0 AS display_order, 'All eligible IOS movements' AS group_label
  UNION ALL SELECT 1, 'Transfer > Transfer > Reorg Department and/or Manager Change'
  UNION ALL SELECT 2, 'Transfer > Transfer > Lateral IOS'
  UNION ALL SELECT 3, 'Transfer > Transfer > Country-to-Country Location Change'
  UNION ALL SELECT 4, 'Promotion > Transfer > Promo IOS'
  UNION ALL SELECT 5, 'Transfer > Transfer > Immigration Parking'
  UNION ALL SELECT 6, 'Demotion > Transfer > Downlevel IOS'
),
reason_cohorts AS (
  SELECT snapshot_key, snapshot_date, reason_value AS group_label, employee_id
  FROM eligible_events
  GROUP BY 1, 2, 3, 4
),
total_cohorts AS (
  SELECT snapshot_key, snapshot_date, 'All eligible IOS movements' AS group_label, employee_id
  FROM eligible_events
  GROUP BY 1, 2, 3, 4
),
cohorts AS (
  SELECT snapshot_key, snapshot_date, group_label, employee_id FROM total_cohorts
  UNION ALL
  SELECT snapshot_key, snapshot_date, group_label, employee_id FROM reason_cohorts
),
cohort_counts AS (
  SELECT snapshot_key, group_label, COUNT(DISTINCT employee_id) AS cohort_employees
  FROM cohorts
  GROUP BY 1, 2
),
voluntary_terms AS (
  SELECT DISTINCT employeeid, term_date::date AS term_date
  FROM hrda.all_terminations
  WHERE term_date::date > DATE '2025-08-24'
    AND term_date::date <= DATE '2026-08-23'
    AND NULLIF(TRIM(term_type), '') = 'Voluntary'
),
baseline_outcomes AS (
  SELECT
    c.group_label,
    COUNT(DISTINCT CASE WHEN t.employeeid IS NOT NULL THEN c.employee_id END) AS voluntary_exit_employees
  FROM cohorts c
  LEFT JOIN voluntary_terms t
    ON t.employeeid = c.employee_id
  WHERE c.snapshot_key = 'baseline'
  GROUP BY 1
),
published AS (
  SELECT
    g.display_order,
    g.group_label,
    current_population.active_regular_employees AS current_active_regular_employees,
    COALESCE(current_cohort.cohort_employees, 0) AS current_cohort_n,
    baseline_population.active_regular_employees AS baseline_active_regular_employees,
    COALESCE(baseline_cohort.cohort_employees, 0) AS baseline_cohort_n,
    COALESCE(outcomes.voluntary_exit_employees, 0) AS annual_voluntary_exit_n
  FROM group_order g
  CROSS JOIN (SELECT active_regular_employees FROM population WHERE snapshot_key = 'current') current_population
  CROSS JOIN (SELECT active_regular_employees FROM population WHERE snapshot_key = 'baseline') baseline_population
  LEFT JOIN cohort_counts current_cohort
    ON current_cohort.snapshot_key = 'current'
   AND current_cohort.group_label = g.group_label
  LEFT JOIN cohort_counts baseline_cohort
    ON baseline_cohort.snapshot_key = 'baseline'
   AND baseline_cohort.group_label = g.group_label
  LEFT JOIN baseline_outcomes outcomes
    ON outcomes.group_label = g.group_label
)
SELECT
  display_order,
  group_label,
  current_active_regular_employees,
  current_cohort_n,
  ROUND(100.0 * current_cohort_n / NULLIF(current_active_regular_employees, 0), 2) AS current_workforce_share_percent,
  baseline_active_regular_employees,
  baseline_cohort_n,
  annual_voluntary_exit_n,
  ROUND(100.0 * annual_voluntary_exit_n / NULLIF(baseline_cohort_n, 0), 2) AS annual_voluntary_attrition_percent,
  CASE WHEN baseline_cohort_n >= 30 THEN 'publish' ELSE 'internal_analysis_exception' END AS publication_status
FROM published
ORDER BY display_order;
