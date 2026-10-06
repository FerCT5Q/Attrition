-- Residential manager-distance: country-label observability for GeoNames mapping.
--
-- Question: Which stored employee or same-snapshot-manager country categories
-- with a publishable aggregate cohort require an ISO normalization rule before
-- public postal centroids can be matched?
--
-- Population/grain: active regular employee-manager pairs at 2026-08-23,
-- one qualified employee-manager pair per employee.  Only aggregate country
-- categories with n >= 30 are returned. No employee IDs, postal values,
-- addresses, or hashes leave the query.
--
-- Acceptance rule: every returned country label must be mapped to a supported
-- public GeoNames country source or remain explicitly not calculable in the
-- frozen aggregate evidence. A missing mapping must never fall forward to an
-- office location, a different snapshot, or an imputed centroid.

WITH snapshot_date_param AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
active_employee_rows AS (
    SELECT
        d.fis_mo_end_dt AS snapshot_date,
        NULLIF(TRIM(CAST(d.employee_id AS VARCHAR(128))), '') AS employee_id,
        NULLIF(TRIM(CAST(d.manager_employee_id AS VARCHAR(128))), '') AS manager_employee_id,
        NULLIF(TRIM(CAST(d.postal_code AS VARCHAR(64))), '') AS postal_code,
        NULLIF(TRIM(CAST(d.country AS VARCHAR(128))), '') AS country,
        d.employee_type
    FROM hrda.post_hire_monthly_worker_dtls d
    JOIN snapshot_date_param s
      ON d.fis_mo_end_dt = s.snapshot_date
    WHERE d.worker_type = 'Employee'
      AND d.active_status = 1
      AND NULLIF(TRIM(CAST(d.employee_id AS VARCHAR(128))), '') IS NOT NULL
),
employee_snapshot_state AS (
    SELECT
        snapshot_date,
        employee_id,
        MIN(manager_employee_id) AS selected_manager_employee_id,
        MIN(postal_code) AS selected_postal_code,
        MIN(country) AS selected_country,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT manager_employee_id) AS manager_id_count,
        COUNT(DISTINCT postal_code) AS postal_code_count,
        COUNT(DISTINCT country) AS country_count,
        MAX(CASE WHEN employee_type = 'Regular' THEN 1 ELSE 0 END) AS is_regular_employee
    FROM active_employee_rows
    GROUP BY snapshot_date, employee_id
),
qualified_pairs AS (
    SELECT
        e.employee_id,
        e.selected_country AS employee_country,
        m.selected_country AS manager_country
    FROM employee_snapshot_state e
    JOIN employee_snapshot_state m
      ON e.snapshot_date = m.snapshot_date
     AND e.selected_manager_employee_id = m.employee_id
    WHERE e.is_regular_employee = 1
      AND e.source_row_count = 1
      AND e.manager_id_count = 1
      AND e.postal_code_count = 1
      AND e.country_count = 1
      AND m.source_row_count = 1
      AND m.postal_code_count = 1
      AND m.country_count = 1
),
party_country AS (
    SELECT employee_id, 'Employee postal country' AS party, employee_country AS country
    FROM qualified_pairs
    UNION ALL
    SELECT employee_id, 'Manager postal country' AS party, manager_country AS country
    FROM qualified_pairs
)
SELECT
    party,
    country,
    COUNT(DISTINCT employee_id) AS employee_manager_pair_count
FROM party_country
GROUP BY party, country
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY party, employee_manager_pair_count DESC, country;
