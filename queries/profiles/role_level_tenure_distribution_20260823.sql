-- internal_analysis | aggregate-only | frozen distribution input
--
-- Population: active regular employees at fis_mo_end_dt = 2026-08-23.
-- Role clock: later of time_in_job_profile_start_date and max_hire_rehire_date.
-- Level clock: later of levelentrydate and max_hire_rehire_date, only when
--              job_level_primary_position is populated.
--
-- Anniversary bands are deliberately shared by both clocks.  This query emits
-- zero-count bands; the evidence builder then pools adjacent bands identically
-- if either clock has a sub-threshold visible bucket.

WITH
parameters AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
target_by_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS source_rows,
        MAX(time_in_job_profile_start_date) AS time_in_job_profile_start_date,
        MAX(levelentrydate) AS levelentrydate,
        MAX(max_hire_rehire_date) AS max_hire_rehire_date,
        MAX(NULLIF(TRIM(job_level_primary_position), '')) AS job_level_primary_position
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM parameters)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND employee_id IS NOT NULL
    GROUP BY employee_id
),
target_unique AS (
    SELECT
        employee_id,
        source_rows,
        time_in_job_profile_start_date,
        levelentrydate,
        max_hire_rehire_date,
        job_level_primary_position
    FROM target_by_employee
    WHERE source_rows = 1
),
clock_starts AS (
    SELECT
        employee_id,
        CASE
            WHEN time_in_job_profile_start_date IS NULL
              OR max_hire_rehire_date IS NULL
              OR time_in_job_profile_start_date > (SELECT snapshot_date FROM parameters)
              OR max_hire_rehire_date > (SELECT snapshot_date FROM parameters)
            THEN NULL
            WHEN time_in_job_profile_start_date < max_hire_rehire_date THEN max_hire_rehire_date
            ELSE time_in_job_profile_start_date
        END AS role_effective_start_date,
        CASE
            WHEN levelentrydate IS NULL
              OR job_level_primary_position IS NULL
              OR max_hire_rehire_date IS NULL
              OR levelentrydate > (SELECT snapshot_date FROM parameters)
              OR max_hire_rehire_date > (SELECT snapshot_date FROM parameters)
            THEN NULL
            WHEN levelentrydate < max_hire_rehire_date THEN max_hire_rehire_date
            ELSE levelentrydate
        END AS level_effective_start_date
    FROM target_unique
),
role_bands AS (
    SELECT
        CASE
            WHEN DATEADD(year, 1, role_effective_start_date) > (SELECT snapshot_date FROM parameters) THEN 'lt_1'
            WHEN DATEADD(year, 2, role_effective_start_date) > (SELECT snapshot_date FROM parameters) THEN 'y1_to_lt2'
            WHEN DATEADD(year, 3, role_effective_start_date) > (SELECT snapshot_date FROM parameters) THEN 'y2_to_lt3'
            WHEN DATEADD(year, 5, role_effective_start_date) > (SELECT snapshot_date FROM parameters) THEN 'y3_to_lt5'
            WHEN DATEADD(year, 10, role_effective_start_date) > (SELECT snapshot_date FROM parameters) THEN 'y5_to_lt10'
            ELSE 'y10_plus'
        END AS bucket_key
    FROM clock_starts
    WHERE role_effective_start_date IS NOT NULL
),
level_bands AS (
    SELECT
        CASE
            WHEN DATEADD(year, 1, level_effective_start_date) > (SELECT snapshot_date FROM parameters) THEN 'lt_1'
            WHEN DATEADD(year, 2, level_effective_start_date) > (SELECT snapshot_date FROM parameters) THEN 'y1_to_lt2'
            WHEN DATEADD(year, 3, level_effective_start_date) > (SELECT snapshot_date FROM parameters) THEN 'y2_to_lt3'
            WHEN DATEADD(year, 5, level_effective_start_date) > (SELECT snapshot_date FROM parameters) THEN 'y3_to_lt5'
            WHEN DATEADD(year, 10, level_effective_start_date) > (SELECT snapshot_date FROM parameters) THEN 'y5_to_lt10'
            ELSE 'y10_plus'
        END AS bucket_key
    FROM clock_starts
    WHERE level_effective_start_date IS NOT NULL
),
bands AS (
    SELECT 1 AS band_order, 'lt_1' AS bucket_key
    UNION ALL SELECT 2, 'y1_to_lt2'
    UNION ALL SELECT 3, 'y2_to_lt3'
    UNION ALL SELECT 4, 'y3_to_lt5'
    UNION ALL SELECT 5, 'y5_to_lt10'
    UNION ALL SELECT 6, 'y10_plus'
),
role_counts AS (
    SELECT bucket_key, COUNT(*)::BIGINT AS employee_count
    FROM role_bands
    GROUP BY bucket_key
),
level_counts AS (
    SELECT bucket_key, COUNT(*)::BIGINT AS employee_count
    FROM level_bands
    GROUP BY bucket_key
)
SELECT snapshot_date, clock, row_type, bucket_key, employee_count
FROM (
    SELECT
        (SELECT snapshot_date FROM parameters) AS snapshot_date,
        'role' AS clock,
        'metric' AS row_type,
        'calculable' AS bucket_key,
        COUNT(*)::BIGINT AS employee_count,
        0 AS sort_order
    FROM role_bands

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'role',
        'metric',
        'not_calculable',
        ((SELECT COUNT(*) FROM target_unique) - (SELECT COUNT(*) FROM role_bands))::BIGINT,
        0

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'level',
        'metric',
        'calculable',
        COUNT(*)::BIGINT,
        0
    FROM level_bands

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'level',
        'metric',
        'not_calculable',
        ((SELECT COUNT(*) FROM target_unique) - (SELECT COUNT(*) FROM level_bands))::BIGINT,
        0

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'role',
        'band',
        bands.bucket_key,
        COALESCE(role_counts.employee_count, 0)::BIGINT,
        bands.band_order
    FROM bands
    LEFT JOIN role_counts ON role_counts.bucket_key = bands.bucket_key

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'level',
        'band',
        bands.bucket_key,
        COALESCE(level_counts.employee_count, 0)::BIGINT,
        bands.band_order
    FROM bands
    LEFT JOIN level_counts ON level_counts.bucket_key = bands.bucket_key
) aggregate_distribution
ORDER BY clock, row_type, sort_order, bucket_key;
