/*
  V7 navigation slide 38: annual team-member attrition by the manager's
  within-team compensation-review state.

  The visual counts managers.  Its attrition pill is deliberately labelled
  "team attrition": the denominator is active regular direct reports assigned
  to managers in the displayed state at the historical snapshot.  This avoids
  relabelling a manager-count distribution as if it were employee count.
  Exact pay, currencies, manager IDs and employee IDs remain inside the query.
*/
WITH source_bounds AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
complete_snapshot_dates AS (
    SELECT snapshot_date
    FROM (
        SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
               ROW_NUMBER() OVER (ORDER BY CAST(fis_mo_end_dt AS DATE) DESC) AS recency_rank
        FROM hrda.post_hire_monthly_worker_dtls
        CROSS JOIN source_bounds
        WHERE fis_mo_end_dt IS NOT NULL
          AND CAST(fis_mo_end_dt AS DATE) <= DATEADD(month, -12, latest_snapshot_date)
        GROUP BY 1
    ) ranked
    WHERE recency_rank <= 24
),
active_report_raw AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.manager_employee_id AS BIGINT)) AS manager_employee_id,
        MAX(NULLIF(TRIM(CAST(w.country AS VARCHAR(128))), '')) AS country,
        MAX(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(128))), '')) AS compensation_grade,
        MAX(NULLIF(TRIM(CAST(w.fte_annual_base_pay_currency_code AS VARCHAR(64))), '')) AS currency_code,
        MAX(w.fte_annual_base_pay) AS fte_annual_base_pay,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_variants,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.country AS VARCHAR(128))), ''), '<NULL>')) AS country_variants,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(128))), ''), '<NULL>')) AS grade_variants,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.fte_annual_base_pay_currency_code AS VARCHAR(64))), ''), '<NULL>')) AS currency_variants,
        COUNT(DISTINCT COALESCE(CAST(w.fte_annual_base_pay AS VARCHAR(64)), '<NULL>')) AS pay_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN complete_snapshot_dates AS d
      ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2
),
report_quality AS (
    SELECT
        COUNT(*) AS active_report_employee_snapshot_count,
        COUNT(DISTINCT snapshot_date) AS snapshot_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN manager_variants > 1 OR country_variants > 1 OR grade_variants > 1
                   OR currency_variants > 1 OR pay_variants > 1 THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count
    FROM active_report_raw
),
complete_members AS (
    SELECT snapshot_date, employee_id, manager_employee_id, country, compensation_grade, currency_code, fte_annual_base_pay
    FROM active_report_raw
    WHERE manager_employee_id IS NOT NULL
      AND country IS NOT NULL
      AND compensation_grade IS NOT NULL
      AND currency_code IS NOT NULL
      AND fte_annual_base_pay IS NOT NULL
      AND fte_annual_base_pay > 0
),
country_grade_currency_groups AS (
    SELECT
        snapshot_date,
        manager_employee_id,
        country,
        compensation_grade,
        currency_code,
        COUNT(*) AS group_size,
        MIN(fte_annual_base_pay) AS minimum_fte_annual_base_pay,
        MAX(fte_annual_base_pay) AS maximum_fte_annual_base_pay
    FROM complete_members
    GROUP BY 1, 2, 3, 4, 5
),
eligible_groups AS (
    SELECT
        snapshot_date,
        manager_employee_id,
        CASE WHEN maximum_fte_annual_base_pay / NULLIF(minimum_fte_annual_base_pay, 0) >= 1.10 THEN 1 ELSE 0 END AS pay_spread_flag
    FROM country_grade_currency_groups
    WHERE group_size >= 2
),
manager_universe AS (
    SELECT DISTINCT snapshot_date, manager_employee_id
    FROM active_report_raw
    WHERE manager_employee_id IS NOT NULL
),
manager_group_counts AS (
    SELECT snapshot_date, manager_employee_id, COUNT(*) AS eligible_group_count, SUM(pay_spread_flag) AS flagged_group_count
    FROM eligible_groups
    GROUP BY 1, 2
),
manager_states AS (
    SELECT
        u.snapshot_date,
        u.manager_employee_id,
        COALESCE(g.eligible_group_count, 0) AS eligible_group_count,
        COALESCE(g.flagged_group_count, 0) AS flagged_group_count,
        CASE WHEN g.manager_employee_id IS NULL THEN 'no_comparable_groups' ELSE 'comparable' END AS manager_state
    FROM manager_universe AS u
    LEFT JOIN manager_group_counts AS g
      ON g.snapshot_date = u.snapshot_date
     AND g.manager_employee_id = u.manager_employee_id
),
voluntary_events AS (
    SELECT CAST(employee_id AS BIGINT) AS employee_id, CAST(term_date AS DATE) AS term_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date IS NOT NULL
    GROUP BY 1, 2
),
classified_reports AS (
    SELECT
        r.snapshot_date,
        r.employee_id,
        s.manager_state,
        s.eligible_group_count,
        s.flagged_group_count,
        MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS annual_voluntary_attrition_target
    FROM active_report_raw AS r
    INNER JOIN manager_states AS s
      ON s.snapshot_date = r.snapshot_date
     AND s.manager_employee_id = r.manager_employee_id
    LEFT JOIN voluntary_events AS v
      ON v.employee_id = r.employee_id
     AND v.term_date > r.snapshot_date
     AND v.term_date <= DATEADD(month, 12, r.snapshot_date)
    WHERE r.manager_employee_id IS NOT NULL
    GROUP BY 1, 2, 3, 4, 5
),
category_rows AS (
    SELECT
        'within_team_review_count' AS metric,
        CASE
          WHEN flagged_group_count = 0 THEN 'No groups to review'
          WHEN flagged_group_count = 1 THEN '1 group to review'
          WHEN flagged_group_count = 2 THEN '2 groups to review'
          WHEN flagged_group_count = 3 THEN '3 groups to review'
          WHEN flagged_group_count BETWEEN 4 AND 7 THEN '4–7 groups to review'
          ELSE '8+ groups to review'
        END AS category,
        snapshot_date, employee_id, annual_voluntary_attrition_target
    FROM classified_reports
    WHERE manager_state = 'comparable'
    UNION ALL
    SELECT
        'within_team_review_share',
        CASE
          WHEN flagged_group_count = 0 THEN '0.0%'
          WHEN 100.0 * flagged_group_count / NULLIF(eligible_group_count, 0) < 50 THEN '>0–<50.0%'
          WHEN 100.0 * flagged_group_count / NULLIF(eligible_group_count, 0) < 75 THEN '50–<75.0%'
          WHEN 100.0 * flagged_group_count / NULLIF(eligible_group_count, 0) < 100 THEN '75–<100.0%'
          ELSE '100.0%'
        END,
        snapshot_date, employee_id, annual_voluntary_attrition_target
    FROM classified_reports
    WHERE manager_state = 'comparable'
    UNION ALL
    SELECT 'within_team_no_comparable', 'No comparable groups', snapshot_date, employee_id, annual_voluntary_attrition_target
    FROM classified_reports
    WHERE manager_state = 'no_comparable_groups'
),
category_metrics AS (
    SELECT
        metric,
        category,
        MIN(snapshot_date) AS first_snapshot_date,
        MAX(snapshot_date) AS last_snapshot_date,
        COUNT(DISTINCT employee_id) AS distinct_employee_count,
        COUNT(*) AS employee_snapshot_count,
        SUM(annual_voluntary_attrition_target) AS voluntary_exits,
        ROUND(100.0 * SUM(annual_voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS annual_attrition_rate_percent
    FROM category_rows
    GROUP BY 1, 2
)
SELECT
    'category' AS row_type,
    metric,
    category,
    first_snapshot_date,
    last_snapshot_date,
    distinct_employee_count,
    employee_snapshot_count,
    voluntary_exits,
    annual_attrition_rate_percent,
    CAST(NULL AS BIGINT) AS diagnostic_value
FROM category_metrics
UNION ALL
SELECT
    'diagnostic', metric, CAST(NULL AS VARCHAR(256)),
    CAST(NULL AS DATE), CAST(NULL AS DATE), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), diagnostic_value
FROM (
    SELECT 'snapshot_count' AS metric, snapshot_count::BIGINT AS diagnostic_value FROM report_quality
    UNION ALL SELECT 'active_report_employee_snapshot_count', active_report_employee_snapshot_count::BIGINT FROM report_quality
    UNION ALL SELECT 'duplicate_employee_snapshot_count', duplicate_employee_snapshot_count::BIGINT FROM report_quality
    UNION ALL SELECT 'conflicting_employee_snapshot_count', conflicting_employee_snapshot_count::BIGINT FROM report_quality
    UNION ALL SELECT 'manager_state_count', COUNT(*)::BIGINT FROM manager_states
) diagnostics
ORDER BY row_type, metric, category;
