-- Region display and U.S. Labor Market drill-down at the approved monthly cutoff.
-- Deliverable: internal_analysis presentation evidence; aggregate results only.
-- Population: active regular employees at fis_mo_end_dt = 2026-08-23.
WITH source_snapshot AS (
    SELECT
        employee_id,
        region,
        country,
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
        COUNT(DISTINCT COALESCE(country, '<NULL>')) AS country_value_count,
        COUNT(DISTINCT COALESCE(labor_market, '<NULL>')) AS labor_market_value_count,
        MIN(region) AS region,
        MIN(country) AS country,
        MIN(labor_market) AS labor_market
    FROM source_snapshot
    GROUP BY employee_id
),
categorized AS (
    SELECT
        employee_id,
        source_row_count,
        region_value_count,
        country_value_count,
        labor_market_value_count,
        region,
        country,
        labor_market,
        CASE
            WHEN country = 'United States of America' THEN 'United States'
            WHEN region = 'AMERICAS' THEN 'Americas excluding U.S.'
            WHEN region = 'INDIA' THEN 'India'
            WHEN region = 'APAC' THEN 'APAC'
            WHEN region = 'EMEA' THEN 'EMEA'
            ELSE 'Unclassified region'
        END AS display_group
    FROM employee_snapshot
),
population AS (
    SELECT COUNT(*) AS eligible_employees
    FROM categorized
),
global_distribution AS (
    SELECT
        display_group AS category,
        CASE display_group
            WHEN 'India' THEN 1
            WHEN 'United States' THEN 2
            WHEN 'APAC' THEN 3
            WHEN 'EMEA' THEN 4
            WHEN 'Americas excluding U.S.' THEN 5
            ELSE 99
        END AS sort_order,
        COUNT(*) AS employee_count
    FROM categorized
    GROUP BY display_group
),
global_labor_market_base AS (
    SELECT
        COALESCE(labor_market, 'Missing Labor Market') AS category,
        COUNT(*) AS employee_count
    FROM categorized
    GROUP BY COALESCE(labor_market, 'Missing Labor Market')
),
global_labor_market_ranked AS (
    SELECT
        category,
        ROW_NUMBER() OVER (ORDER BY employee_count DESC, category) AS sort_order,
        employee_count
    FROM global_labor_market_base
),
global_labor_market_distribution AS (
    SELECT
        category,
        sort_order,
        employee_count
    FROM global_labor_market_ranked
    WHERE sort_order <= 20

    UNION ALL

    SELECT
        'Other Labor Markets' AS category,
        21 AS sort_order,
        SUM(employee_count) AS employee_count
    FROM global_labor_market_ranked
    WHERE sort_order > 20
    HAVING SUM(employee_count) > 0
),
us_labor_market_distribution AS (
    SELECT
        COALESCE(labor_market, 'Missing Labor Market') AS category,
        CASE COALESCE(labor_market, 'Missing Labor Market')
            WHEN 'USA - Market 1' THEN 1
            WHEN 'USA - Market 2' THEN 2
            WHEN 'USA - Market 3' THEN 3
            WHEN 'Missing Labor Market' THEN 98
            ELSE 99
        END AS sort_order,
        COUNT(*) AS employee_count
    FROM categorized
    WHERE country = 'United States of America'
    GROUP BY COALESCE(labor_market, 'Missing Labor Market')
),
india_labor_market_distribution AS (
    SELECT
        COALESCE(labor_market, 'Missing Labor Market') AS category,
        1 AS sort_order,
        COUNT(*) AS employee_count
    FROM categorized
    WHERE country = 'India'
    GROUP BY COALESCE(labor_market, 'Missing Labor Market')
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

    SELECT 'employees_with_conflicting_country_values', COUNT(*)
    FROM categorized
    WHERE country_value_count <> 1

    UNION ALL

    SELECT 'employees_with_conflicting_labor_market_values', COUNT(*)
    FROM categorized
    WHERE labor_market_value_count <> 1

    UNION ALL

    SELECT 'unclassified_region_employees', COUNT(*)
    FROM categorized
    WHERE display_group = 'Unclassified region'

    UNION ALL

    SELECT 'united_states_outside_americas', COUNT(*)
    FROM categorized
    WHERE country = 'United States of America'
      AND COALESCE(region, '<NULL>') <> 'AMERICAS'

    UNION ALL

    SELECT 'india_outside_india_region', COUNT(*)
    FROM categorized
    WHERE country = 'India'
      AND COALESCE(region, '<NULL>') <> 'INDIA'

    UNION ALL

    SELECT 'united_states_missing_labor_market', COUNT(*)
    FROM categorized
    WHERE country = 'United States of America'
      AND labor_market IS NULL

    UNION ALL

    SELECT 'india_missing_labor_market', COUNT(*)
    FROM categorized
    WHERE country = 'India'
      AND labor_market IS NULL

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
    'global_region' AS result_type,
    'Global display groups' AS scope,
    distribution.category,
    distribution.sort_order,
    distribution.employee_count,
    CAST(100.0 * distribution.employee_count / NULLIF(population.eligible_employees, 0) AS DECIMAL(18, 6)) AS percentage
FROM global_distribution AS distribution
CROSS JOIN population

UNION ALL

SELECT
    'global_labor_market' AS result_type,
    'All eligible employees' AS scope,
    distribution.category,
    distribution.sort_order,
    distribution.employee_count,
    CAST(100.0 * distribution.employee_count / NULLIF(population.eligible_employees, 0) AS DECIMAL(18, 6)) AS percentage
FROM global_labor_market_distribution AS distribution
CROSS JOIN population

UNION ALL

SELECT
    'metadata' AS result_type,
    'Global Labor Market domain' AS scope,
    'observed_source_categories' AS category,
    1 AS sort_order,
    COUNT(*) AS employee_count,
    CAST(NULL AS DECIMAL(18, 6)) AS percentage
FROM global_labor_market_base

UNION ALL

SELECT
    'us_labor_market' AS result_type,
    'United States only' AS scope,
    distribution.category,
    distribution.sort_order,
    distribution.employee_count,
    CAST(
        100.0 * distribution.employee_count
        / NULLIF((SELECT COUNT(*) FROM categorized WHERE country = 'United States of America'), 0)
        AS DECIMAL(18, 6)
    ) AS percentage
FROM us_labor_market_distribution AS distribution

UNION ALL

SELECT
    'india_labor_market' AS result_type,
    'India only' AS scope,
    distribution.category,
    distribution.sort_order,
    distribution.employee_count,
    CAST(
        100.0 * distribution.employee_count
        / NULLIF((SELECT COUNT(*) FROM categorized WHERE country = 'India'), 0)
        AS DECIMAL(18, 6)
    ) AS percentage
FROM india_labor_market_distribution AS distribution

UNION ALL

SELECT
    'validation' AS result_type,
    'Snapshot mapping checks' AS scope,
    category,
    99 AS sort_order,
    employee_count,
    CAST(NULL AS DECIMAL(18, 6)) AS percentage
FROM validation_metrics
ORDER BY result_type, sort_order, category;
