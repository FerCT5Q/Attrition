-- Global Region and Labor Market display at the approved monthly cutoff.
-- Deliverable: internal_analysis presentation evidence; aggregate results only.
-- Population: active regular employees at fis_mo_end_dt = 2026-08-23.
WITH source_snapshot AS (
    SELECT
        employee_id,
        NULLIF(TRIM(region), '') AS region,
        NULLIF(TRIM(labor_market), '') AS labor_market
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt = DATE '2026-08-23'
),
employee_snapshot AS (
    SELECT
        employee_id,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(region, '<NULL>')) AS region_value_count,
        COUNT(DISTINCT COALESCE(labor_market, '<NULL>')) AS labor_market_value_count,
        MIN(region) AS region,
        MIN(labor_market) AS labor_market
    FROM source_snapshot
    GROUP BY employee_id
),
categorized AS (
    SELECT
        employee_id,
        source_row_count,
        region_value_count,
        labor_market_value_count,
        region,
        labor_market,
        CASE region
            WHEN 'INDIA' THEN 'India'
            WHEN 'AMERICAS' THEN 'Americas'
            WHEN 'APAC' THEN 'APAC'
            WHEN 'EMEA' THEN 'EMEA'
            ELSE 'Unclassified region'
        END AS display_region
    FROM employee_snapshot
),
population AS (
    SELECT COUNT(*) AS eligible_employees
    FROM categorized
),
region_distribution AS (
    SELECT
        display_region AS category,
        CASE display_region
            WHEN 'India' THEN 1
            WHEN 'Americas' THEN 2
            WHEN 'APAC' THEN 3
            WHEN 'EMEA' THEN 4
            ELSE 99
        END AS sort_order,
        COUNT(*) AS employee_count
    FROM categorized
    GROUP BY display_region
),
labor_market_base AS (
    SELECT
        COALESCE(labor_market, 'Missing Labor Market') AS category,
        COUNT(*) AS employee_count
    FROM categorized
    GROUP BY COALESCE(labor_market, 'Missing Labor Market')
),
labor_market_ranked AS (
    SELECT
        category,
        ROW_NUMBER() OVER (ORDER BY employee_count DESC, category) AS sort_order,
        employee_count
    FROM labor_market_base
),
labor_market_distribution AS (
    SELECT category, sort_order, employee_count
    FROM labor_market_ranked
    WHERE sort_order <= 20

    UNION ALL

    SELECT 'Other Labor Markets', 21, SUM(employee_count)
    FROM labor_market_ranked
    WHERE sort_order > 20
    HAVING SUM(employee_count) > 0
),
validation_metrics AS (
    SELECT 'employees_with_multiple_source_rows' AS category, COUNT(*) AS employee_count
    FROM categorized
    WHERE source_row_count <> 1

    UNION ALL

    SELECT 'employees_with_conflicting_region_values', COUNT(*)
    FROM categorized
    WHERE region_value_count <> 1

    UNION ALL

    SELECT 'employees_with_conflicting_labor_market_values', COUNT(*)
    FROM categorized
    WHERE labor_market_value_count <> 1

    UNION ALL

    SELECT 'unclassified_region_employees', COUNT(*)
    FROM categorized
    WHERE display_region = 'Unclassified region'

    UNION ALL

    SELECT 'global_missing_labor_market', COUNT(*)
    FROM categorized
    WHERE labor_market IS NULL
)
SELECT
    'population' AS result_type,
    'Active regular employees' AS scope,
    'Eligible employees' AS category,
    1 AS sort_order,
    eligible_employees AS employee_count,
    CAST(100.000000 AS DECIMAL(18, 6)) AS percentage
FROM population

UNION ALL

SELECT
    'global_region',
    'Stored Region categories',
    distribution.category,
    distribution.sort_order,
    distribution.employee_count,
    CAST(100.0 * distribution.employee_count / NULLIF(population.eligible_employees, 0) AS DECIMAL(18, 6))
FROM region_distribution AS distribution
CROSS JOIN population

UNION ALL

SELECT
    'global_labor_market',
    'All eligible employees',
    distribution.category,
    distribution.sort_order,
    distribution.employee_count,
    CAST(100.0 * distribution.employee_count / NULLIF(population.eligible_employees, 0) AS DECIMAL(18, 6))
FROM labor_market_distribution AS distribution
CROSS JOIN population

UNION ALL

SELECT
    'metadata',
    'Global Labor Market domain',
    'observed_source_categories',
    1,
    COUNT(*),
    CAST(NULL AS DECIMAL(18, 6))
FROM labor_market_base

UNION ALL

SELECT
    'validation',
    'Snapshot mapping checks',
    category,
    99,
    employee_count,
    CAST(NULL AS DECIMAL(18, 6))
FROM validation_metrics
ORDER BY result_type, sort_order, category;
