-- Purpose: validate the proposed team-membership route for
-- "Within team compensation range" at the fixed deck cutoff.
--
-- Proposed derived-feature rule (not a final compensation definition):
-- a team is the set of active regular employees whose manager_employee_id is
-- the same in the same employee snapshot. The manager is resolved against the
-- active Employee roster in that snapshot. No manager identifiers or
-- compensation values are returned.
--
-- Acceptance rule for membership feasibility:
--   * zero duplicate employee keys in the regular-active and active-Employee
--     snapshot rosters; and
--   * at least 95% of regular active report rows with a non-null manager
--     resolve to exactly one active Employee manager record.
--
-- The report-count fields are diagnostic controls only. A flag corroborates
-- membership if it is non-null and positive for at least 95% of resolved
-- teams. Exact equality is reported but is not required, because a stored
-- flag may count a broader worker scope than active regular direct reports.
--
-- This does not approve the comparable population, percentile/band formula,
-- small-team fallback, or compa_ratio lineage. Those decisions remain
-- necessary before publishing a compensation distribution.

WITH active_employee_raw AS (
    SELECT employee_id, reg_non_intern_dir_reports, all_dir_reports
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
active_employee_roster AS (
    SELECT r.employee_id, r.reg_non_intern_dir_reports, r.all_dir_reports
    FROM active_employee_raw r
    JOIN active_employee_key_counts k
      ON r.employee_id = k.employee_id
    WHERE k.row_count = 1
),
regular_report_raw AS (
    SELECT employee_id, manager_employee_id
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
    SELECT r.employee_id, r.manager_employee_id
    FROM regular_report_raw r
    JOIN regular_report_key_counts k
      ON r.employee_id = k.employee_id
    WHERE k.row_count = 1
),
team_groups AS (
    SELECT manager_employee_id, COUNT(*) AS observed_regular_direct_reports
    FROM regular_reporters
    WHERE manager_employee_id IS NOT NULL
    GROUP BY 1
),
resolved_teams AS (
    SELECT
        t.observed_regular_direct_reports,
        m.employee_id AS resolved_manager_employee_id,
        m.reg_non_intern_dir_reports,
        m.all_dir_reports
    FROM team_groups t
    LEFT JOIN active_employee_roster m
      ON t.manager_employee_id = m.employee_id
),
integrity_summary AS (
    SELECT
        (SELECT COUNT(*) FROM active_employee_raw) AS active_employee_rows,
        (SELECT COUNT(DISTINCT employee_id) FROM active_employee_raw) AS active_employee_distinct,
        (SELECT COALESCE(SUM(CASE WHEN row_count > 1 THEN 1 ELSE 0 END), 0) FROM active_employee_key_counts) AS active_employee_duplicate_keys,
        (SELECT COALESCE(SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END), 0) FROM active_employee_key_counts) AS active_employee_duplicate_extra_rows,
        (SELECT COUNT(*) FROM regular_report_raw) AS regular_active_rows,
        (SELECT COUNT(DISTINCT employee_id) FROM regular_report_raw) AS regular_active_distinct,
        (SELECT COALESCE(SUM(CASE WHEN row_count > 1 THEN 1 ELSE 0 END), 0) FROM regular_report_key_counts) AS regular_active_duplicate_keys,
        (SELECT COALESCE(SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END), 0) FROM regular_report_key_counts) AS regular_active_duplicate_extra_rows
),
membership_summary AS (
    SELECT
        (SELECT COUNT(*) FROM regular_reporters) AS regular_active_unique_rows,
        (SELECT COUNT(*) FROM regular_reporters WHERE manager_employee_id IS NOT NULL) AS report_rows_with_manager,
        (SELECT COUNT(*) FROM regular_reporters WHERE manager_employee_id IS NULL) AS report_rows_without_manager,
        COUNT(*) AS direct_manager_teams,
        SUM(CASE WHEN resolved_manager_employee_id IS NOT NULL THEN 1 ELSE 0 END) AS resolved_manager_teams,
        SUM(CASE WHEN resolved_manager_employee_id IS NULL THEN 1 ELSE 0 END) AS unresolved_manager_teams,
        SUM(CASE WHEN resolved_manager_employee_id IS NOT NULL THEN observed_regular_direct_reports ELSE 0 END) AS resolved_report_rows,
        SUM(CASE WHEN resolved_manager_employee_id IS NULL THEN observed_regular_direct_reports ELSE 0 END) AS unresolved_report_rows,
        SUM(CASE WHEN observed_regular_direct_reports >= 30 THEN 1 ELSE 0 END) AS teams_ge30,
        SUM(CASE WHEN observed_regular_direct_reports >= 30 THEN observed_regular_direct_reports ELSE 0 END) AS report_rows_in_teams_ge30
    FROM resolved_teams
),
flag_summary AS (
    SELECT
        SUM(CASE WHEN resolved_manager_employee_id IS NOT NULL THEN 1 ELSE 0 END) AS resolved_manager_teams,
        SUM(CASE WHEN resolved_manager_employee_id IS NOT NULL
                  AND reg_non_intern_dir_reports IS NOT NULL
                  AND reg_non_intern_dir_reports > 0 THEN 1 ELSE 0 END) AS reg_non_intern_flag_positive_teams,
        SUM(CASE WHEN resolved_manager_employee_id IS NOT NULL
                  AND all_dir_reports IS NOT NULL
                  AND all_dir_reports > 0 THEN 1 ELSE 0 END) AS all_dir_flag_positive_teams,
        SUM(CASE WHEN resolved_manager_employee_id IS NOT NULL
                  AND reg_non_intern_dir_reports = observed_regular_direct_reports THEN 1 ELSE 0 END) AS reg_non_intern_exact_match_teams,
        SUM(CASE WHEN resolved_manager_employee_id IS NOT NULL
                  AND all_dir_reports = observed_regular_direct_reports THEN 1 ELSE 0 END) AS all_dir_exact_match_teams,
        SUM(CASE WHEN resolved_manager_employee_id IS NOT NULL
                  AND (reg_non_intern_dir_reports IS NULL OR reg_non_intern_dir_reports <= 0) THEN 1 ELSE 0 END) AS reg_non_intern_missing_or_zero_teams,
        SUM(CASE WHEN resolved_manager_employee_id IS NOT NULL
                  AND (all_dir_reports IS NULL OR all_dir_reports <= 0) THEN 1 ELSE 0 END) AS all_dir_missing_or_zero_teams
    FROM resolved_teams
),
team_size_bands AS (
    SELECT
        CASE
            WHEN observed_regular_direct_reports >= 30 THEN '30+'
            WHEN observed_regular_direct_reports >= 10 THEN '10-29'
            WHEN observed_regular_direct_reports >= 5 THEN '05-09'
            ELSE '01-04'
        END AS team_size_band,
        COUNT(*) AS team_count,
        SUM(observed_regular_direct_reports) AS report_rows
    FROM resolved_teams
    GROUP BY 1
)
SELECT 'integrity' AS section, 'active_employee_rows' AS metric,
       active_employee_rows::BIGINT AS numerator, NULL::BIGINT AS denominator,
       NULL::DECIMAL(18,4) AS percent_value
FROM integrity_summary
UNION ALL
SELECT 'integrity', 'active_employee_distinct', active_employee_distinct::BIGINT, NULL::BIGINT, NULL::DECIMAL(18,4)
FROM integrity_summary
UNION ALL
SELECT 'integrity', 'active_employee_duplicate_keys', active_employee_duplicate_keys::BIGINT, NULL::BIGINT, NULL::DECIMAL(18,4)
FROM integrity_summary
UNION ALL
SELECT 'integrity', 'active_employee_duplicate_extra_rows', active_employee_duplicate_extra_rows::BIGINT, NULL::BIGINT, NULL::DECIMAL(18,4)
FROM integrity_summary
UNION ALL
SELECT 'integrity', 'regular_active_rows', regular_active_rows::BIGINT, NULL::BIGINT, NULL::DECIMAL(18,4)
FROM integrity_summary
UNION ALL
SELECT 'integrity', 'regular_active_distinct', regular_active_distinct::BIGINT, NULL::BIGINT, NULL::DECIMAL(18,4)
FROM integrity_summary
UNION ALL
SELECT 'integrity', 'regular_active_duplicate_keys', regular_active_duplicate_keys::BIGINT, NULL::BIGINT, NULL::DECIMAL(18,4)
FROM integrity_summary
UNION ALL
SELECT 'integrity', 'regular_active_duplicate_extra_rows', regular_active_duplicate_extra_rows::BIGINT, NULL::BIGINT, NULL::DECIMAL(18,4)
FROM integrity_summary
UNION ALL
SELECT 'membership', 'regular_active_unique_rows', regular_active_unique_rows::BIGINT, NULL::BIGINT, NULL::DECIMAL(18,4)
FROM membership_summary
UNION ALL
SELECT 'membership', 'report_rows_with_manager', report_rows_with_manager::BIGINT, regular_active_unique_rows::BIGINT,
       ROUND(100.0 * report_rows_with_manager / NULLIF(regular_active_unique_rows, 0), 4)
FROM membership_summary
UNION ALL
SELECT 'membership', 'report_rows_without_manager', report_rows_without_manager::BIGINT, regular_active_unique_rows::BIGINT,
       ROUND(100.0 * report_rows_without_manager / NULLIF(regular_active_unique_rows, 0), 4)
FROM membership_summary
UNION ALL
SELECT 'membership', 'direct_manager_teams', direct_manager_teams::BIGINT, NULL::BIGINT, NULL::DECIMAL(18,4)
FROM membership_summary
UNION ALL
SELECT 'membership', 'resolved_manager_teams', resolved_manager_teams::BIGINT, direct_manager_teams::BIGINT,
       ROUND(100.0 * resolved_manager_teams / NULLIF(direct_manager_teams, 0), 4)
FROM membership_summary
UNION ALL
SELECT 'membership', 'unresolved_manager_teams', unresolved_manager_teams::BIGINT, direct_manager_teams::BIGINT,
       ROUND(100.0 * unresolved_manager_teams / NULLIF(direct_manager_teams, 0), 4)
FROM membership_summary
UNION ALL
SELECT 'membership', 'resolved_report_rows', resolved_report_rows::BIGINT, report_rows_with_manager::BIGINT,
       ROUND(100.0 * resolved_report_rows / NULLIF(report_rows_with_manager, 0), 4)
FROM membership_summary
UNION ALL
SELECT 'membership', 'unresolved_report_rows', unresolved_report_rows::BIGINT, report_rows_with_manager::BIGINT,
       ROUND(100.0 * unresolved_report_rows / NULLIF(report_rows_with_manager, 0), 4)
FROM membership_summary
UNION ALL
SELECT 'membership', 'report_rows_in_teams_ge30', report_rows_in_teams_ge30::BIGINT, report_rows_with_manager::BIGINT,
       ROUND(100.0 * report_rows_in_teams_ge30 / NULLIF(report_rows_with_manager, 0), 4)
FROM membership_summary
UNION ALL
SELECT 'flags', 'reg_non_intern_dir_reports_positive', reg_non_intern_flag_positive_teams::BIGINT, resolved_manager_teams::BIGINT,
       ROUND(100.0 * reg_non_intern_flag_positive_teams / NULLIF(resolved_manager_teams, 0), 4)
FROM flag_summary
UNION ALL
SELECT 'flags', 'all_dir_reports_positive', all_dir_flag_positive_teams::BIGINT, resolved_manager_teams::BIGINT,
       ROUND(100.0 * all_dir_flag_positive_teams / NULLIF(resolved_manager_teams, 0), 4)
FROM flag_summary
UNION ALL
SELECT 'flags', 'reg_non_intern_dir_reports_exact_match', reg_non_intern_exact_match_teams::BIGINT, resolved_manager_teams::BIGINT,
       ROUND(100.0 * reg_non_intern_exact_match_teams / NULLIF(resolved_manager_teams, 0), 4)
FROM flag_summary
UNION ALL
SELECT 'flags', 'all_dir_reports_exact_match', all_dir_exact_match_teams::BIGINT, resolved_manager_teams::BIGINT,
       ROUND(100.0 * all_dir_exact_match_teams / NULLIF(resolved_manager_teams, 0), 4)
FROM flag_summary
UNION ALL
SELECT 'flags', 'reg_non_intern_dir_reports_missing_or_zero', reg_non_intern_missing_or_zero_teams::BIGINT, resolved_manager_teams::BIGINT,
       ROUND(100.0 * reg_non_intern_missing_or_zero_teams / NULLIF(resolved_manager_teams, 0), 4)
FROM flag_summary
UNION ALL
SELECT 'flags', 'all_dir_reports_missing_or_zero', all_dir_missing_or_zero_teams::BIGINT, resolved_manager_teams::BIGINT,
       ROUND(100.0 * all_dir_missing_or_zero_teams / NULLIF(resolved_manager_teams, 0), 4)
FROM flag_summary
UNION ALL
SELECT 'team_size_band', team_size_band, report_rows::BIGINT, team_count::BIGINT,
       NULL::DECIMAL(18,4)
FROM team_size_bands
ORDER BY 1, 2;
