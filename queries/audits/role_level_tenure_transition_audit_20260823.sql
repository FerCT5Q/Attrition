-- internal_analysis | aggregate-only | purpose-built publication audit
--
-- Claim tested before publication:
--   The 2026-08-23 active-regular snapshot is unique at employee-snapshot
--   grain, the two stored start dates are usable with the rehire adjustment,
--   and changes in job_level_primary_position reconcile to levelentrydate.
--
-- This query deliberately uses job_code and job_title only as aggregate
-- supporting proxies for job-profile-date behaviour.  Neither proxy defines
-- a job profile and neither value is emitted.
--
-- Acceptance rule:
--   No duplicate or conflicting target/history employee-snapshot rows, no
--   future start or rehire dates, no rehire flag without a usable rehire date,
--   and no unexplained detailed-level transition or reset.  Event flags are
--   diagnostics only; they do not define a reset.

WITH
parameters AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
target_source AS (
    SELECT
        employee_id,
        time_in_job_profile_start_date,
        levelentrydate,
        max_hire_rehire_date,
        NULLIF(TRIM(job_level_primary_position), '') AS job_level_primary_position,
        time_in_role,
        is_promo,
        is_demoted,
        is_transferred,
        is_rehire
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM parameters)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND employee_id IS NOT NULL
),
target_by_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(CAST(time_in_job_profile_start_date AS VARCHAR(32)), '__NULL__')) AS role_start_values,
        COUNT(DISTINCT COALESCE(CAST(levelentrydate AS VARCHAR(32)), '__NULL__')) AS level_start_values,
        COUNT(DISTINCT COALESCE(CAST(max_hire_rehire_date AS VARCHAR(32)), '__NULL__')) AS rehire_date_values,
        COUNT(DISTINCT COALESCE(job_level_primary_position, '__NULL__')) AS detailed_level_values,
        MAX(time_in_job_profile_start_date) AS time_in_job_profile_start_date,
        MAX(levelentrydate) AS levelentrydate,
        MAX(max_hire_rehire_date) AS max_hire_rehire_date,
        MAX(job_level_primary_position) AS job_level_primary_position,
        MAX(time_in_role) AS time_in_role,
        MAX(COALESCE(is_rehire, 0)) AS is_rehire
    FROM target_source
    GROUP BY employee_id
),
target_unique AS (
    SELECT
        employee_id,
        source_rows,
        time_in_job_profile_start_date,
        levelentrydate,
        max_hire_rehire_date,
        job_level_primary_position,
        time_in_role,
        is_rehire
    FROM target_by_employee
    WHERE source_rows = 1
),
history_source AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        NULLIF(TRIM(job_level_primary_position), '') AS job_level_primary_position,
        levelentrydate,
        time_in_job_profile_start_date,
        max_hire_rehire_date,
        NULLIF(TRIM(job_code), '') AS job_code,
        NULLIF(TRIM(job_title), '') AS job_title,
        COALESCE(is_promo, 0) AS is_promo,
        COALESCE(is_demoted, 0) AS is_demoted,
        COALESCE(is_transferred, 0) AS is_transferred,
        COALESCE(is_rehire, 0) AS is_rehire
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt <= (SELECT snapshot_date FROM parameters)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND employee_id IS NOT NULL
),
history_by_snapshot AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(CAST(levelentrydate AS VARCHAR(32)), '__NULL__')) AS level_start_values,
        COUNT(DISTINCT COALESCE(CAST(time_in_job_profile_start_date AS VARCHAR(32)), '__NULL__')) AS role_start_values,
        COUNT(DISTINCT COALESCE(CAST(max_hire_rehire_date AS VARCHAR(32)), '__NULL__')) AS rehire_date_values,
        COUNT(DISTINCT COALESCE(job_level_primary_position, '__NULL__')) AS detailed_level_values,
        COUNT(DISTINCT COALESCE(job_code, '__NULL__')) AS job_code_values,
        COUNT(DISTINCT COALESCE(job_title, '__NULL__')) AS job_title_values,
        MAX(job_level_primary_position) AS job_level_primary_position,
        MAX(levelentrydate) AS levelentrydate,
        MAX(time_in_job_profile_start_date) AS time_in_job_profile_start_date,
        MAX(max_hire_rehire_date) AS max_hire_rehire_date,
        MAX(job_code) AS job_code,
        MAX(job_title) AS job_title,
        MAX(is_promo) AS is_promo,
        MAX(is_demoted) AS is_demoted,
        MAX(is_transferred) AS is_transferred,
        MAX(is_rehire) AS is_rehire
    FROM history_source
    GROUP BY employee_id, fis_mo_end_dt
),
history_unique AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        source_rows,
        job_level_primary_position,
        levelentrydate,
        time_in_job_profile_start_date,
        max_hire_rehire_date,
        job_code,
        job_title,
        is_promo,
        is_demoted,
        is_transferred,
        is_rehire
    FROM history_by_snapshot
    WHERE source_rows = 1
),
history_with_previous AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        job_level_primary_position,
        levelentrydate,
        time_in_job_profile_start_date,
        max_hire_rehire_date,
        job_code,
        job_title,
        is_promo,
        is_demoted,
        is_transferred,
        is_rehire,
        LAG(fis_mo_end_dt) OVER (PARTITION BY employee_id ORDER BY fis_mo_end_dt) AS previous_snapshot_date,
        LAG(job_level_primary_position) OVER (PARTITION BY employee_id ORDER BY fis_mo_end_dt) AS previous_detailed_level,
        LAG(levelentrydate) OVER (PARTITION BY employee_id ORDER BY fis_mo_end_dt) AS previous_levelentrydate,
        LAG(time_in_job_profile_start_date) OVER (PARTITION BY employee_id ORDER BY fis_mo_end_dt) AS previous_job_profile_start_date,
        LAG(max_hire_rehire_date) OVER (PARTITION BY employee_id ORDER BY fis_mo_end_dt) AS previous_max_hire_rehire_date,
        LAG(job_code) OVER (PARTITION BY employee_id ORDER BY fis_mo_end_dt) AS previous_job_code,
        LAG(job_title) OVER (PARTITION BY employee_id ORDER BY fis_mo_end_dt) AS previous_job_title
    FROM history_unique
),
transition_population AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        job_level_primary_position,
        levelentrydate,
        time_in_job_profile_start_date,
        max_hire_rehire_date,
        job_code,
        job_title,
        is_promo,
        is_demoted,
        is_transferred,
        is_rehire,
        previous_snapshot_date,
        previous_detailed_level,
        previous_levelentrydate,
        previous_job_profile_start_date,
        previous_max_hire_rehire_date,
        previous_job_code,
        previous_job_title
    FROM history_with_previous
    WHERE previous_snapshot_date IS NOT NULL
      AND DATEDIFF(day, previous_snapshot_date, fis_mo_end_dt) BETWEEN 20 AND 45
),
transition_flags AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        job_level_primary_position,
        levelentrydate,
        time_in_job_profile_start_date,
        max_hire_rehire_date,
        job_code,
        job_title,
        is_promo,
        is_demoted,
        is_transferred,
        is_rehire,
        previous_snapshot_date,
        previous_detailed_level,
        previous_levelentrydate,
        previous_job_profile_start_date,
        previous_max_hire_rehire_date,
        previous_job_code,
        previous_job_title,
        CASE
            WHEN job_level_primary_position IS NOT NULL
             AND previous_detailed_level IS NOT NULL
             AND job_level_primary_position <> previous_detailed_level
            THEN 1 ELSE 0
        END AS detailed_level_changed,
        CASE
            WHEN levelentrydate > previous_snapshot_date
             AND levelentrydate <= fis_mo_end_dt
            THEN 1 ELSE 0
        END AS level_start_reset_in_interval,
        CASE
            WHEN time_in_job_profile_start_date > previous_snapshot_date
             AND time_in_job_profile_start_date <= fis_mo_end_dt
            THEN 1 ELSE 0
        END AS job_profile_start_reset_in_interval,
        CASE
            WHEN max_hire_rehire_date > previous_snapshot_date
             AND max_hire_rehire_date <= fis_mo_end_dt
            THEN 1 ELSE 0
        END AS rehire_in_interval,
        CASE
            WHEN COALESCE(job_code, '__NULL__') <> COALESCE(previous_job_code, '__NULL__')
              OR COALESCE(job_title, '__NULL__') <> COALESCE(previous_job_title, '__NULL__')
            THEN 1 ELSE 0
        END AS job_proxy_changed
    FROM transition_population
)
SELECT snapshot_date, 'metric' AS row_type, metric, metric_value
FROM (
    SELECT
        (SELECT snapshot_date FROM parameters) AS snapshot_date,
        'target_source_row_count' AS metric,
        COUNT(*)::BIGINT AS metric_value
    FROM target_source

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'target_unique_employee_count',
        COUNT(*)::BIGINT
    FROM target_by_employee

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'target_duplicate_employee_count',
        COALESCE(SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_by_employee

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'target_duplicate_row_excess_count',
        COALESCE(SUM(CASE WHEN source_rows > 1 THEN source_rows - 1 ELSE 0 END), 0)::BIGINT
    FROM target_by_employee

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'target_conflicting_employee_count',
        COALESCE(SUM(CASE WHEN source_rows > 1 AND (
            role_start_values > 1 OR level_start_values > 1 OR rehire_date_values > 1 OR detailed_level_values > 1
        ) THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_by_employee

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'role_start_future_date_count',
        COALESCE(SUM(CASE WHEN time_in_job_profile_start_date > (SELECT snapshot_date FROM parameters) THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'level_start_future_date_count',
        COALESCE(SUM(CASE WHEN levelentrydate > (SELECT snapshot_date FROM parameters) THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'rehire_date_future_count',
        COALESCE(SUM(CASE WHEN max_hire_rehire_date > (SELECT snapshot_date FROM parameters) THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'rehire_flag_without_date_count',
        COALESCE(SUM(CASE WHEN is_rehire = 1 AND max_hire_rehire_date IS NULL THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'role_calculable_employee_count',
        COALESCE(SUM(CASE WHEN time_in_job_profile_start_date IS NOT NULL
                              AND max_hire_rehire_date IS NOT NULL
                              AND time_in_job_profile_start_date <= (SELECT snapshot_date FROM parameters)
                              AND max_hire_rehire_date <= (SELECT snapshot_date FROM parameters)
                         THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'level_calculable_employee_count',
        COALESCE(SUM(CASE WHEN levelentrydate IS NOT NULL
                              AND job_level_primary_position IS NOT NULL
                              AND max_hire_rehire_date IS NOT NULL
                              AND levelentrydate <= (SELECT snapshot_date FROM parameters)
                              AND max_hire_rehire_date <= (SELECT snapshot_date FROM parameters)
                         THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'role_rehire_adjustment_count',
        COALESCE(SUM(CASE WHEN time_in_job_profile_start_date IS NOT NULL
                              AND max_hire_rehire_date IS NOT NULL
                              AND time_in_job_profile_start_date < max_hire_rehire_date
                         THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'level_rehire_adjustment_count',
        COALESCE(SUM(CASE WHEN levelentrydate IS NOT NULL
                              AND max_hire_rehire_date IS NOT NULL
                              AND levelentrydate < max_hire_rehire_date
                         THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'time_in_role_support_populated_count',
        COALESCE(SUM(CASE WHEN time_in_role IS NOT NULL THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'history_duplicate_employee_snapshot_count',
        COALESCE(SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM history_by_snapshot

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'history_conflicting_employee_snapshot_count',
        COALESCE(SUM(CASE WHEN source_rows > 1 AND (
            level_start_values > 1 OR role_start_values > 1 OR rehire_date_values > 1
            OR detailed_level_values > 1 OR job_code_values > 1 OR job_title_values > 1
        ) THEN 1 ELSE 0 END), 0)::BIGINT
    FROM history_by_snapshot

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'comparable_transition_snapshot_count',
        COUNT(*)::BIGINT
    FROM transition_population

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'detailed_level_transition_count',
        COALESCE(SUM(detailed_level_changed), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'detailed_level_transition_with_date_reset_count',
        COALESCE(SUM(CASE WHEN detailed_level_changed = 1 AND level_start_reset_in_interval = 1 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'unexplained_detailed_level_transition_count',
        COALESCE(SUM(CASE WHEN detailed_level_changed = 1
                              AND level_start_reset_in_interval = 0
                              AND rehire_in_interval = 0
                         THEN 1 ELSE 0 END), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'unexplained_detailed_level_reset_count',
        COALESCE(SUM(CASE WHEN detailed_level_changed = 0
                              AND level_start_reset_in_interval = 1
                              AND rehire_in_interval = 0
                         THEN 1 ELSE 0 END), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'job_profile_start_reset_count',
        COALESCE(SUM(job_profile_start_reset_in_interval), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'job_profile_reset_with_proxy_change_count',
        COALESCE(SUM(CASE WHEN job_profile_start_reset_in_interval = 1 AND job_proxy_changed = 1 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'job_profile_reset_without_proxy_change_count',
        COALESCE(SUM(CASE WHEN job_profile_start_reset_in_interval = 1 AND job_proxy_changed = 0 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'job_proxy_change_without_profile_reset_count',
        COALESCE(SUM(CASE WHEN job_proxy_changed = 1 AND job_profile_start_reset_in_interval = 0 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'promotion_level_transition_intersection_count',
        COALESCE(SUM(CASE WHEN is_promo = 1 AND detailed_level_changed = 1 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'demotion_level_transition_intersection_count',
        COALESCE(SUM(CASE WHEN is_demoted = 1 AND detailed_level_changed = 1 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'transfer_level_transition_intersection_count',
        COALESCE(SUM(CASE WHEN is_transferred = 1 AND detailed_level_changed = 1 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM transition_flags

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'rehire_level_transition_intersection_count',
        COALESCE(SUM(CASE WHEN rehire_in_interval = 1 AND detailed_level_changed = 1 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM transition_flags
) aggregate_metrics
ORDER BY metric;
