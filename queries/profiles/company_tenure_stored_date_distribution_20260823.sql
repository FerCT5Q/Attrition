-- internal_analysis | aggregate-only | fixed Company tenure profile
--
-- Population: active regular employees at fis_mo_end_dt = 2026-08-23.
-- Left clock: original_hire_date exactly as stored.
-- Right clock: max_hire_rehire_date exactly as stored.
--
-- The profile deliberately does not take the later of the two dates.  Each
-- distribution is a direct description of its own stored field.  Anniversary
-- bands are shared and zero-count bands are emitted for validation.

WITH
parameters AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
target_by_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS source_rows,
        MAX(original_hire_date) AS original_hire_date,
        MAX(max_hire_rehire_date) AS max_hire_rehire_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM parameters)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND employee_id IS NOT NULL
    GROUP BY employee_id
),
target_unique AS (
    SELECT employee_id, original_hire_date, max_hire_rehire_date
    FROM target_by_employee
    WHERE source_rows = 1
),
clock_dates AS (
    SELECT 'original_hire' AS clock, original_hire_date AS start_date
    FROM target_unique
    UNION ALL
    SELECT 'latest_hire_rehire' AS clock, max_hire_rehire_date AS start_date
    FROM target_unique
),
classified AS (
    SELECT
        clock,
        CASE
            WHEN start_date IS NULL OR start_date > (SELECT snapshot_date FROM parameters) THEN NULL
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 1, start_date) THEN 'lt_1'
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 2, start_date) THEN 'y1_to_lt2'
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 3, start_date) THEN 'y2_to_lt3'
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 5, start_date) THEN 'y3_to_lt5'
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 10, start_date) THEN 'y5_to_lt10'
            ELSE 'y10_plus'
        END AS bucket_key
    FROM clock_dates
),
clock_metrics AS (
    SELECT
        (SELECT snapshot_date FROM parameters) AS snapshot_date,
        clock,
        'metric' AS row_type,
        'calculable' AS bucket_key,
        COUNT(CASE WHEN bucket_key IS NOT NULL THEN 1 END)::BIGINT AS employee_count
    FROM classified
    GROUP BY clock

    UNION ALL

    SELECT
        (SELECT snapshot_date FROM parameters),
        clock,
        'metric',
        'not_calculable',
        COUNT(CASE WHEN bucket_key IS NULL THEN 1 END)::BIGINT
    FROM classified
    GROUP BY clock
),
bands AS (
    SELECT 'lt_1' AS bucket_key, 1 AS band_order
    UNION ALL SELECT 'y1_to_lt2', 2
    UNION ALL SELECT 'y2_to_lt3', 3
    UNION ALL SELECT 'y3_to_lt5', 4
    UNION ALL SELECT 'y5_to_lt10', 5
    UNION ALL SELECT 'y10_plus', 6
),
band_counts AS (
    SELECT
        (SELECT snapshot_date FROM parameters) AS snapshot_date,
        clocks.clock,
        'band' AS row_type,
        bands.bucket_key,
        COUNT(classified.bucket_key)::BIGINT AS employee_count,
        bands.band_order
    FROM (SELECT DISTINCT clock FROM classified) clocks
    CROSS JOIN bands
    LEFT JOIN classified
      ON classified.clock = clocks.clock
     AND classified.bucket_key = bands.bucket_key
    GROUP BY clocks.clock, bands.bucket_key, bands.band_order
)
SELECT snapshot_date, clock, row_type, bucket_key, employee_count
FROM (
    SELECT snapshot_date, clock, row_type, bucket_key, employee_count, 0 AS band_order
    FROM clock_metrics
    UNION ALL
    SELECT snapshot_date, clock, row_type, bucket_key, employee_count, band_order
    FROM band_counts
) profile_rows
ORDER BY
    CASE clock WHEN 'original_hire' THEN 1 WHEN 'latest_hire_rehire' THEN 2 ELSE 3 END,
    CASE row_type WHEN 'metric' THEN 1 WHEN 'band' THEN 2 ELSE 3 END,
    CASE bucket_key
        WHEN 'calculable' THEN 1
        WHEN 'not_calculable' THEN 2
        WHEN 'lt_1' THEN 1
        WHEN 'y1_to_lt2' THEN 2
        WHEN 'y2_to_lt3' THEN 3
        WHEN 'y3_to_lt5' THEN 4
        WHEN 'y5_to_lt10' THEN 5
        WHEN 'y10_plus' THEN 6
        ELSE 99
    END;
