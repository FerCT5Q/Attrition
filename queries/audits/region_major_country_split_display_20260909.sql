-- Display-only Region alternative: United States / Americas residual and
-- China / APAC residual at the approved monthly cutoff.
-- Deliverable: internal_analysis evidence; aggregate results only.
-- Population: active regular employees at fis_mo_end_dt = 2026-08-23.
WITH source_snapshot AS (
    SELECT
        employee_id,
        NULLIF(TRIM(region), '') AS region,
        NULLIF(TRIM(country), '') AS country
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
        MIN(region) AS region,
        MIN(country) AS country
    FROM source_snapshot
    GROUP BY employee_id
),
categorized AS (
    SELECT
        employee_id,
        source_row_count,
        region_value_count,
        country_value_count,
        region,
        country,
        CASE
            WHEN region = 'INDIA' THEN 'India'
            WHEN country = 'United States of America' THEN 'United States'
            WHEN region = 'AMERICAS' THEN 'Americas excluding U.S.'
            WHEN country = 'China' THEN 'China'
            WHEN region = 'APAC' THEN 'APAC excluding China'
            WHEN region = 'EMEA' THEN 'EMEA'
            ELSE 'Unclassified region'
        END AS display_group
    FROM employee_snapshot
),
population AS (
    SELECT COUNT(*) AS eligible_employees
    FROM categorized
),
display_distribution AS (
    SELECT
        display_group AS category,
        CASE display_group
            WHEN 'India' THEN 1
            WHEN 'United States' THEN 2
            WHEN 'Americas excluding U.S.' THEN 3
            WHEN 'China' THEN 4
            WHEN 'APAC excluding China' THEN 5
            WHEN 'EMEA' THEN 6
            ELSE 99
        END AS sort_order,
        COUNT(*) AS employee_count
    FROM categorized
    GROUP BY display_group
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

    SELECT 'unclassified_region_employees', COUNT(*)
    FROM categorized
    WHERE region NOT IN ('INDIA', 'AMERICAS', 'APAC', 'EMEA') OR region IS NULL

    UNION ALL

    SELECT 'united_states_outside_americas', COUNT(*)
    FROM categorized
    WHERE country = 'United States of America'
      AND COALESCE(region, '<NULL>') <> 'AMERICAS'

    UNION ALL

    SELECT 'china_outside_apac', COUNT(*)
    FROM categorized
    WHERE country = 'China'
      AND COALESCE(region, '<NULL>') <> 'APAC'

    UNION ALL

    SELECT 'missing_country_employees', COUNT(*)
    FROM categorized
    WHERE country IS NULL
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
    'major_country_split',
    'Display-only Region grouping',
    distribution.category,
    distribution.sort_order,
    distribution.employee_count,
    CAST(100.0 * distribution.employee_count / NULLIF(population.eligible_employees, 0) AS DECIMAL(18, 6))
FROM display_distribution AS distribution
CROSS JOIN population

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
