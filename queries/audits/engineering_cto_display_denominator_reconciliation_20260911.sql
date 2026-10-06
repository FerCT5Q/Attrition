-- Aggregate-only reconciliation for the Engineering slide denominator.
--
-- Claim: the lower CTO display must use the same current snapshot universe as
-- the frozen upper eng_or_noneng chart.  The frozen upper chart contains
-- 50,033 employee snapshots at 2026-08-23.  This query compares that frozen
-- count with current Redshift variants and reports no employee-level values.
--
-- Acceptance rule:
--   * identify the current active Regular Employee population without adding
--     an RF360 filter;
--   * quantify any difference from the frozen upper-chart denominator;
--   * report source-row and distinct-employee reconciliation, including
--     duplicate employee keys.
WITH snapshot_choice AS (
    SELECT DATE '2026-08-23' AS snapshot_date,
           CAST(50033 AS BIGINT) AS frozen_upper_chart_employee_count
),
base AS (
    SELECT
        CAST(employee_id AS VARCHAR(64)) AS employee_id,
        active_status,
        NULLIF(TRIM(CAST(is_rf360_yes_no AS VARCHAR(64))), '') AS rf360_value,
        NULLIF(TRIM(CAST(eng_or_noneng AS VARCHAR(128))), '') AS eng_or_noneng
    FROM hrda.post_hire_monthly_worker_dtls
    CROSS JOIN snapshot_choice
    WHERE fis_mo_end_dt = snapshot_choice.snapshot_date
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND employee_id IS NOT NULL
),
variant_rows AS (
    SELECT 'active_regular_no_rf_filter' AS variant, employee_id
    FROM base
    WHERE active_status = 1

    UNION ALL

    SELECT 'active_regular_rf360_zero', employee_id
    FROM base
    WHERE active_status = 1
      AND rf360_value = '0'

    UNION ALL

    SELECT 'active_regular_rf360_one', employee_id
    FROM base
    WHERE active_status = 1
      AND rf360_value = '1'

    UNION ALL

    SELECT 'active_regular_rf360_null', employee_id
    FROM base
    WHERE active_status = 1
      AND rf360_value IS NULL

    UNION ALL

    SELECT 'active_regular_no_rf_filter_eng_observable', employee_id
    FROM base
    WHERE active_status = 1
      AND eng_or_noneng IS NOT NULL

    UNION ALL

    SELECT 'active_regular_rf360_zero_eng_observable', employee_id
    FROM base
    WHERE active_status = 1
      AND rf360_value = '0'
      AND eng_or_noneng IS NOT NULL
),
variant_employee AS (
    SELECT variant, employee_id, COUNT(*) AS source_row_count
    FROM variant_rows
    GROUP BY 1, 2
),
reconciled AS (
    SELECT
        variant,
        SUM(source_row_count) AS source_row_count,
        COUNT(*) AS distinct_employee_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_count
    FROM variant_employee
    GROUP BY 1
)
SELECT
    snapshot_choice.snapshot_date,
    reconciled.variant,
    reconciled.source_row_count,
    reconciled.distinct_employee_count,
    reconciled.duplicate_employee_count,
    snapshot_choice.frozen_upper_chart_employee_count,
    reconciled.distinct_employee_count - snapshot_choice.frozen_upper_chart_employee_count AS difference_to_frozen_upper_chart
FROM reconciled
CROSS JOIN snapshot_choice
ORDER BY reconciled.variant;
