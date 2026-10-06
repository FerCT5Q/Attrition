-- Presentation profile for the agreed manager-level descriptive metric.
-- It returns only aggregate manager counts.  Raw salary values, manager IDs,
-- country/grade/currency labels, and employee rows remain inside the query.

WITH active_employee_raw AS (
    SELECT employee_id, reg_non_intern_dir_reports
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt::date = DATE '2026-08-23'
      AND worker_type = 'Employee'
      AND active_status = 1
),
active_employee_key_counts AS (
    SELECT employee_id, COUNT(*) AS row_count
    FROM active_employee_raw
    GROUP BY 1
),
active_employee_unique AS (
    SELECT r.employee_id, r.reg_non_intern_dir_reports
    FROM active_employee_raw r
    JOIN active_employee_key_counts k
      ON r.employee_id = k.employee_id
    WHERE k.row_count = 1
),
regular_report_raw AS (
    SELECT
        employee_id,
        manager_employee_id,
        country,
        compensation_grade,
        fte_annual_base_pay,
        fte_annual_base_pay_currency_code
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt::date = DATE '2026-08-23'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
regular_report_key_counts AS (
    SELECT employee_id, COUNT(*) AS row_count
    FROM regular_report_raw
    GROUP BY 1
),
regular_reporters AS (
    SELECT
        r.employee_id,
        r.manager_employee_id,
        r.country,
        r.compensation_grade,
        r.fte_annual_base_pay,
        r.fte_annual_base_pay_currency_code
    FROM regular_report_raw r
    JOIN regular_report_key_counts k
      ON r.employee_id = k.employee_id
    WHERE k.row_count = 1
),
manager_members AS (
    SELECT
        r.employee_id,
        r.manager_employee_id,
        r.country,
        r.compensation_grade,
        r.fte_annual_base_pay,
        r.fte_annual_base_pay_currency_code
    FROM regular_reporters r
    JOIN active_employee_unique m
      ON r.manager_employee_id = m.employee_id
    WHERE r.manager_employee_id IS NOT NULL
      AND m.reg_non_intern_dir_reports > 0
),
complete_members AS (
    SELECT
        manager_employee_id,
        country,
        compensation_grade,
        fte_annual_base_pay_currency_code,
        fte_annual_base_pay
    FROM manager_members
    WHERE country IS NOT NULL AND TRIM(country) <> ''
      AND compensation_grade IS NOT NULL AND TRIM(compensation_grade) <> ''
      AND fte_annual_base_pay_currency_code IS NOT NULL AND TRIM(fte_annual_base_pay_currency_code) <> ''
      AND fte_annual_base_pay IS NOT NULL AND fte_annual_base_pay > 0
),
country_grade_currency_groups AS (
    SELECT
        manager_employee_id,
        country,
        compensation_grade,
        fte_annual_base_pay_currency_code,
        COUNT(*) AS group_size,
        MIN(fte_annual_base_pay) AS minimum_fte_annual_base_pay,
        MAX(fte_annual_base_pay) AS maximum_fte_annual_base_pay
    FROM complete_members
    GROUP BY 1, 2, 3, 4
),
eligible_groups AS (
    SELECT
        manager_employee_id,
        CASE
            WHEN maximum_fte_annual_base_pay / NULLIF(minimum_fte_annual_base_pay, 0) >= 1.10 THEN 1
            ELSE 0
        END AS pay_spread_flag
    FROM country_grade_currency_groups
    WHERE group_size >= 2
),
manager_universe AS (
    SELECT DISTINCT manager_employee_id
    FROM manager_members
),
manager_group_counts AS (
    SELECT
        manager_employee_id,
        COUNT(*) AS eligible_group_count,
        SUM(pay_spread_flag) AS flagged_group_count
    FROM eligible_groups
    GROUP BY 1
),
manager_results AS (
    SELECT
        u.manager_employee_id,
        g.eligible_group_count,
        g.flagged_group_count,
        CASE
            WHEN g.manager_employee_id IS NULL THEN 'no_comparable_groups'
            ELSE 'comparable'
        END AS manager_state
    FROM manager_universe u
    LEFT JOIN manager_group_counts g
      ON u.manager_employee_id = g.manager_employee_id
),
count_distribution AS (
    SELECT
        flagged_group_count::VARCHAR AS bucket_key,
        COUNT(*) AS manager_count
    FROM manager_results
    WHERE manager_state = 'comparable'
    GROUP BY 1
),
rate_distribution AS (
    SELECT
        CASE
            WHEN flagged_group_count = 0 THEN 'rate_0'
            WHEN 100.0 * flagged_group_count / eligible_group_count < 25 THEN 'rate_gt0_lt25'
            WHEN 100.0 * flagged_group_count / eligible_group_count < 50 THEN 'rate_25_lt50'
            WHEN 100.0 * flagged_group_count / eligible_group_count < 75 THEN 'rate_50_lt75'
            WHEN 100.0 * flagged_group_count / eligible_group_count < 100 THEN 'rate_75_lt100'
            ELSE 'rate_100'
        END AS bucket_key,
        COUNT(*) AS manager_count
    FROM manager_results
    WHERE manager_state = 'comparable'
    GROUP BY 1
),
metrics AS (
    SELECT 'manager_universe' AS bucket_key, COUNT(*) AS manager_count
    FROM manager_results
    UNION ALL SELECT 'comparable_managers', COUNT(*) FROM manager_results WHERE manager_state = 'comparable'
    UNION ALL SELECT 'no_comparable_group_managers', COUNT(*) FROM manager_results WHERE manager_state = 'no_comparable_groups'
    UNION ALL SELECT 'eligible_comparable_groups', COALESCE(SUM(eligible_group_count), 0) FROM manager_results WHERE manager_state = 'comparable'
    UNION ALL SELECT 'flagged_comparable_groups', COALESCE(SUM(flagged_group_count), 0) FROM manager_results WHERE manager_state = 'comparable'
)
SELECT
    DATE '2026-08-23' AS snapshot_date,
    'metric' AS row_type,
    bucket_key,
    manager_count::BIGINT AS manager_count
FROM metrics
UNION ALL
SELECT DATE '2026-08-23', 'count_distribution', bucket_key, manager_count::BIGINT
FROM count_distribution
UNION ALL
SELECT DATE '2026-08-23', 'rate_distribution', bucket_key, manager_count::BIGINT
FROM rate_distribution
UNION ALL
SELECT DATE '2026-08-23', 'state', manager_state, COUNT(*)::BIGINT
FROM manager_results
WHERE manager_state = 'no_comparable_groups'
GROUP BY 1, 2, 3
ORDER BY 2, 3;
