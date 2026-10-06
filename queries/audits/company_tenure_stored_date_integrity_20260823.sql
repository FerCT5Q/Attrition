-- internal_analysis | aggregate-only | purpose-built Company tenure audit
--
-- Claim tested before publication:
--   The active-regular population at the fixed 2026-08-23 monthly snapshot
--   is unique at employee-snapshot grain and its two stored date fields can
--   be described independently without future dates or an impossible order.
--
-- This is a stored-field descriptive audit.  It does not choose a governed
-- Company tenure definition and does not apply either date over the other.
--
-- Acceptance rule:
--   Every eligible employee has one non-conflicting snapshot row; there are
--   no future dates and no original_hire_date later than
--   max_hire_rehire_date when both are present.  Profile denominators must
--   reconcile to this same unique fixed-snapshot population.

WITH
parameters AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
population_source AS (
    SELECT
        employee_id,
        original_hire_date,
        max_hire_rehire_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM parameters)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
target_source AS (
    SELECT
        employee_id,
        original_hire_date,
        max_hire_rehire_date
    FROM population_source
    WHERE employee_id IS NOT NULL
),
target_by_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(CAST(original_hire_date AS VARCHAR(32)), '__NULL__')) AS original_hire_values,
        COUNT(DISTINCT COALESCE(CAST(max_hire_rehire_date AS VARCHAR(32)), '__NULL__')) AS latest_hire_rehire_values,
        MAX(original_hire_date) AS original_hire_date,
        MAX(max_hire_rehire_date) AS max_hire_rehire_date
    FROM target_source
    GROUP BY employee_id
),
target_unique AS (
    SELECT
        employee_id,
        original_hire_date,
        max_hire_rehire_date
    FROM target_by_employee
    WHERE source_rows = 1
)
SELECT snapshot_date, 'metric' AS row_type, metric, metric_value
FROM (
    SELECT
        (SELECT snapshot_date FROM parameters) AS snapshot_date,
        'population_source_row_count' AS metric,
        COUNT(*)::BIGINT AS metric_value
    FROM population_source

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'target_missing_employee_id_row_count',
        COUNT(*)::BIGINT
    FROM population_source
    WHERE employee_id IS NULL

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'target_source_row_count',
        COUNT(*)::BIGINT
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
        COALESCE(SUM(CASE WHEN source_rows > 1
                          AND (original_hire_values > 1 OR latest_hire_rehire_values > 1)
                     THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_by_employee

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'original_hire_null_count',
        COALESCE(SUM(CASE WHEN original_hire_date IS NULL THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'latest_hire_rehire_null_count',
        COALESCE(SUM(CASE WHEN max_hire_rehire_date IS NULL THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'original_hire_future_date_count',
        COALESCE(SUM(CASE WHEN original_hire_date > (SELECT snapshot_date FROM parameters) THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'latest_hire_rehire_future_date_count',
        COALESCE(SUM(CASE WHEN max_hire_rehire_date > (SELECT snapshot_date FROM parameters) THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'impossible_date_order_count',
        COALESCE(SUM(CASE WHEN original_hire_date IS NOT NULL
                              AND max_hire_rehire_date IS NOT NULL
                              AND original_hire_date > max_hire_rehire_date
                         THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'original_hire_calculable_employee_count',
        COALESCE(SUM(CASE WHEN original_hire_date IS NOT NULL
                              AND original_hire_date <= (SELECT snapshot_date FROM parameters)
                         THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique

    UNION ALL SELECT
        (SELECT snapshot_date FROM parameters),
        'latest_hire_rehire_calculable_employee_count',
        COALESCE(SUM(CASE WHEN max_hire_rehire_date IS NOT NULL
                              AND max_hire_rehire_date <= (SELECT snapshot_date FROM parameters)
                         THEN 1 ELSE 0 END), 0)::BIGINT
    FROM target_unique
) aggregate_metrics
ORDER BY metric;
