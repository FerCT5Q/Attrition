-- Aggregate-only reconciliation of the frozen upper eng_or_noneng chart.
--
-- The frozen slide contains Engineering=38,440 and Non_Engineering=11,593
-- (50,033 total) at 2026-08-23. The query compares those published counts
-- with the current active Regular Employee snapshot, without returning IDs or
-- employee rows.
--
-- Acceptance rule: the current category counts and total must equal the
-- frozen upper chart before a lower display is allowed to claim direct
-- denominator comparability.
WITH snapshot_choice AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
current_categories AS (
    SELECT
        NULLIF(TRIM(CAST(eng_or_noneng AS VARCHAR(128))), '') AS category,
        COUNT(DISTINCT CAST(employee_id AS VARCHAR(64))) AS current_employee_count
    FROM hrda.post_hire_monthly_worker_dtls
    CROSS JOIN snapshot_choice
    WHERE fis_mo_end_dt = snapshot_choice.snapshot_date
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND employee_id IS NOT NULL
    GROUP BY 1
),
frozen_categories AS (
    SELECT 'Engineering' AS category, CAST(38440 AS BIGINT) AS frozen_employee_count
    UNION ALL
    SELECT 'Non_Engineering', CAST(11593 AS BIGINT)
),
reconciled AS (
    SELECT
        frozen_categories.category,
        COALESCE(current_categories.current_employee_count, 0) AS current_employee_count,
        frozen_categories.frozen_employee_count,
        COALESCE(current_categories.current_employee_count, 0) - frozen_employee_count AS difference_to_frozen
    FROM frozen_categories
    LEFT JOIN current_categories
      ON current_categories.category = frozen_categories.category
),
totals AS (
    SELECT
        SUM(current_employee_count) AS current_total,
        SUM(frozen_employee_count) AS frozen_total,
        SUM(difference_to_frozen) AS total_difference_to_frozen
    FROM reconciled
)
SELECT
    snapshot_choice.snapshot_date,
    reconciled.category,
    reconciled.current_employee_count,
    reconciled.frozen_employee_count,
    reconciled.difference_to_frozen,
    totals.current_total,
    totals.frozen_total,
    totals.total_difference_to_frozen
FROM reconciled
CROSS JOIN totals
CROSS JOIN snapshot_choice
ORDER BY reconciled.category;
