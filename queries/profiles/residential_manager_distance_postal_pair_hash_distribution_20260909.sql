-- Internal-only hashed postal-pair profile for Residential distance from manager.
--
-- This query returns aggregate employee counts by normalized employee-manager
-- postal proxies. Postal codes, employee IDs, manager IDs, addresses, and
-- raw individual rows never leave Redshift. The hash fields are consumed only
-- in process memory by tools/build_residential_manager_distance_evidence.py to
-- join against locally downloaded public GeoNames centroids; they must never
-- be logged, stored in the frozen evidence, or sent to an external service.
--
-- Fixed population: active regular employees at 2026-08-23; manager candidates
-- are active Employees from that same snapshot. Grain: aggregated
-- employee-manager postal-proxy pair.
--
-- Acceptance rule enforced by the builder: the reconciliation audit passes;
-- each postal/country proxy is unique for every selected pair; centroid results
-- reconcile to feature-eligible pairs; and every displayed distance band has
-- n >= 30.

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
        e.selected_postal_code AS employee_postal_code,
        m.selected_country AS manager_country,
        m.selected_postal_code AS manager_postal_code
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
hashed_pairs AS (
    SELECT
        employee_id,
        employee_country,
        manager_country,
        MD5(UPPER(employee_postal_code)) AS employee_postal_hash,
        MD5(REGEXP_REPLACE(UPPER(employee_postal_code), '[^A-Z0-9]', '')) AS employee_postal_hash_compact,
        MD5(LEFT(REGEXP_REPLACE(UPPER(employee_postal_code), '[^A-Z0-9]', ''), 2)) AS employee_postal_hash_prefix_2,
        MD5(LEFT(REGEXP_REPLACE(UPPER(employee_postal_code), '[^A-Z0-9]', ''), 3)) AS employee_postal_hash_prefix_3,
        MD5(LEFT(REGEXP_REPLACE(UPPER(employee_postal_code), '[^A-Z0-9]', ''), 4)) AS employee_postal_hash_prefix_4,
        MD5(LPAD(REGEXP_REPLACE(UPPER(employee_postal_code), '[^A-Z0-9]', ''), 5, '0')) AS employee_postal_hash_zero_pad_5,
        MD5(LPAD(REGEXP_REPLACE(UPPER(employee_postal_code), '[^A-Z0-9]', ''), 6, '0')) AS employee_postal_hash_zero_pad_6,
        MD5(LPAD(REGEXP_REPLACE(UPPER(employee_postal_code), '[^A-Z0-9]', ''), 7, '0')) AS employee_postal_hash_zero_pad_7,
        MD5(UPPER(manager_postal_code)) AS manager_postal_hash,
        MD5(REGEXP_REPLACE(UPPER(manager_postal_code), '[^A-Z0-9]', '')) AS manager_postal_hash_compact,
        MD5(LEFT(REGEXP_REPLACE(UPPER(manager_postal_code), '[^A-Z0-9]', ''), 2)) AS manager_postal_hash_prefix_2,
        MD5(LEFT(REGEXP_REPLACE(UPPER(manager_postal_code), '[^A-Z0-9]', ''), 3)) AS manager_postal_hash_prefix_3,
        MD5(LEFT(REGEXP_REPLACE(UPPER(manager_postal_code), '[^A-Z0-9]', ''), 4)) AS manager_postal_hash_prefix_4,
        MD5(LPAD(REGEXP_REPLACE(UPPER(manager_postal_code), '[^A-Z0-9]', ''), 5, '0')) AS manager_postal_hash_zero_pad_5,
        MD5(LPAD(REGEXP_REPLACE(UPPER(manager_postal_code), '[^A-Z0-9]', ''), 6, '0')) AS manager_postal_hash_zero_pad_6,
        MD5(LPAD(REGEXP_REPLACE(UPPER(manager_postal_code), '[^A-Z0-9]', ''), 7, '0')) AS manager_postal_hash_zero_pad_7
    FROM qualified_pairs
)
SELECT
    employee_country,
    manager_country,
    employee_postal_hash,
    employee_postal_hash_compact,
    employee_postal_hash_prefix_2,
    employee_postal_hash_prefix_3,
    employee_postal_hash_prefix_4,
    employee_postal_hash_zero_pad_5,
    employee_postal_hash_zero_pad_6,
    employee_postal_hash_zero_pad_7,
    manager_postal_hash,
    manager_postal_hash_compact,
    manager_postal_hash_prefix_2,
    manager_postal_hash_prefix_3,
    manager_postal_hash_prefix_4,
    manager_postal_hash_zero_pad_5,
    manager_postal_hash_zero_pad_6,
    manager_postal_hash_zero_pad_7,
    COUNT(DISTINCT employee_id) AS employee_count
FROM hashed_pairs
GROUP BY
    employee_country,
    manager_country,
    employee_postal_hash,
    employee_postal_hash_compact,
    employee_postal_hash_prefix_2,
    employee_postal_hash_prefix_3,
    employee_postal_hash_prefix_4,
    employee_postal_hash_zero_pad_5,
    employee_postal_hash_zero_pad_6,
    employee_postal_hash_zero_pad_7,
    manager_postal_hash,
    manager_postal_hash_compact,
    manager_postal_hash_prefix_2,
    manager_postal_hash_prefix_3,
    manager_postal_hash_prefix_4,
    manager_postal_hash_zero_pad_5,
    manager_postal_hash_zero_pad_6,
    manager_postal_hash_zero_pad_7
ORDER BY
    employee_country,
    manager_country,
    employee_postal_hash,
    manager_postal_hash;
