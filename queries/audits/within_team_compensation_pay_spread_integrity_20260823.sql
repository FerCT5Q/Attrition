-- Purpose: integrity and reconciliation audit for the descriptive
-- Within team compensation range slide at the 2026-08-23 deck cutoff.
--
-- Agreed descriptive rule:
--   team = active regular direct reports sharing manager_employee_id;
--   comparable group = manager + country + compensation_grade + currency;
--   a group is eligible when it has at least two complete direct reports;
--   group flag = max(fte_annual_base_pay) / min(fte_annual_base_pay) >= 1.10.
-- The manager is excluded from their own team.  Manager membership is derived
-- from manager_employee_id and corroborated with reg_non_intern_dir_reports > 0.
-- This query returns only aggregate metrics and never returns identifiers,
-- country/grade/currency labels, or compensation values.

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
member_resolution AS (
    SELECT
        r.employee_id,
        r.manager_employee_id,
        r.country,
        r.compensation_grade,
        r.fte_annual_base_pay,
        r.fte_annual_base_pay_currency_code,
        m.employee_id AS resolved_manager,
        m.reg_non_intern_dir_reports
    FROM regular_reporters r
    LEFT JOIN active_employee_unique m
      ON r.manager_employee_id = m.employee_id
),
manager_members AS (
    SELECT
        employee_id,
        manager_employee_id,
        country,
        compensation_grade,
        fte_annual_base_pay,
        fte_annual_base_pay_currency_code
    FROM member_resolution
    WHERE manager_employee_id IS NOT NULL
      AND resolved_manager IS NOT NULL
      AND reg_non_intern_dir_reports > 0
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
country_grade_currency_conflicts AS (
    SELECT manager_employee_id, country, compensation_grade
    FROM complete_members
    GROUP BY 1, 2, 3
    HAVING COUNT(DISTINCT fte_annual_base_pay_currency_code) > 1
)
SELECT 'target_source_row_count' AS metric, (SELECT COUNT(*) FROM regular_report_raw)::BIGINT AS metric_value
UNION ALL SELECT 'target_unique_employee_count', (SELECT COUNT(*) FROM regular_reporters)::BIGINT
UNION ALL SELECT 'target_duplicate_employee_count', (SELECT COALESCE(SUM(CASE WHEN row_count > 1 THEN 1 ELSE 0 END), 0) FROM regular_report_key_counts)::BIGINT
UNION ALL SELECT 'target_duplicate_row_excess_count', (SELECT COALESCE(SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END), 0) FROM regular_report_key_counts)::BIGINT
UNION ALL SELECT 'active_employee_duplicate_key_count', (SELECT COALESCE(SUM(CASE WHEN row_count > 1 THEN 1 ELSE 0 END), 0) FROM active_employee_key_counts)::BIGINT
UNION ALL SELECT 'active_employee_duplicate_row_excess_count', (SELECT COALESCE(SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END), 0) FROM active_employee_key_counts)::BIGINT
UNION ALL SELECT 'reporter_without_manager_count', (SELECT COUNT(*) FROM regular_reporters WHERE manager_employee_id IS NULL)::BIGINT
UNION ALL SELECT 'reporter_with_unresolved_manager_count', (SELECT COUNT(*) FROM member_resolution WHERE manager_employee_id IS NOT NULL AND resolved_manager IS NULL)::BIGINT
UNION ALL SELECT 'reporter_with_nonpositive_manager_flag_count', (SELECT COUNT(*) FROM member_resolution WHERE manager_employee_id IS NOT NULL AND resolved_manager IS NOT NULL AND COALESCE(reg_non_intern_dir_reports, 0) <= 0)::BIGINT
UNION ALL SELECT 'manager_universe_count', (SELECT COUNT(*) FROM manager_universe)::BIGINT
UNION ALL SELECT 'manager_member_report_count', (SELECT COUNT(*) FROM manager_members)::BIGINT
UNION ALL SELECT 'missing_country_member_count', (SELECT COUNT(*) FROM manager_members WHERE country IS NULL OR TRIM(country) = '')::BIGINT
UNION ALL SELECT 'missing_grade_member_count', (SELECT COUNT(*) FROM manager_members WHERE compensation_grade IS NULL OR TRIM(compensation_grade) = '')::BIGINT
UNION ALL SELECT 'missing_currency_member_count', (SELECT COUNT(*) FROM manager_members WHERE fte_annual_base_pay_currency_code IS NULL OR TRIM(fte_annual_base_pay_currency_code) = '')::BIGINT
UNION ALL SELECT 'invalid_fte_annual_base_pay_member_count', (SELECT COUNT(*) FROM manager_members WHERE fte_annual_base_pay IS NULL OR fte_annual_base_pay <= 0)::BIGINT
UNION ALL SELECT 'complete_member_count', (SELECT COUNT(*) FROM complete_members)::BIGINT
UNION ALL SELECT 'country_grade_currency_conflict_cell_count', (SELECT COUNT(*) FROM country_grade_currency_conflicts)::BIGINT
UNION ALL SELECT 'candidate_group_count', (SELECT COUNT(*) FROM country_grade_currency_groups)::BIGINT
UNION ALL SELECT 'singleton_group_count', (SELECT COUNT(*) FROM country_grade_currency_groups WHERE group_size = 1)::BIGINT
UNION ALL SELECT 'eligible_group_count', (SELECT COUNT(*) FROM eligible_groups)::BIGINT
UNION ALL SELECT 'flagged_eligible_group_count', (SELECT COALESCE(SUM(pay_spread_flag), 0) FROM eligible_groups)::BIGINT
UNION ALL SELECT 'comparable_manager_count', (SELECT COUNT(*) FROM manager_group_counts)::BIGINT
UNION ALL SELECT 'no_comparable_group_manager_count', (SELECT COUNT(*) FROM manager_universe u LEFT JOIN manager_group_counts g ON u.manager_employee_id = g.manager_employee_id WHERE g.manager_employee_id IS NULL)::BIGINT
UNION ALL SELECT 'manager_reconciliation_difference', (SELECT (SELECT COUNT(*) FROM manager_universe) - (SELECT COUNT(*) FROM manager_group_counts) - (SELECT COUNT(*) FROM manager_universe u LEFT JOIN manager_group_counts g ON u.manager_employee_id = g.manager_employee_id WHERE g.manager_employee_id IS NULL))::BIGINT
ORDER BY 1;
