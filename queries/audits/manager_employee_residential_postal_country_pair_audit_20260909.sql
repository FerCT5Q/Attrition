-- Follow-up for the residential postal-pair alternative.
--
-- Why this follow-up is required: a postal code cannot be mapped to a public
-- centroid without a country for both employee and manager; the same code can
-- occur in different countries. This audit is aggregate-only and returns no
-- postal codes, country labels, employee IDs, addresses, or distances.
--
-- Claim tested: at the 2026-08-23 monthly snapshot, after a same-snapshot
-- manager join, each party has exactly one
-- stored postal_code and country. This remains a technical availability check,
-- not authorization to process residential location data or a validation of
-- the proposed home-to-home geographic-distance definition.
--
-- Acceptance rule: at least 30 eligible employees, no employee duplicate rows
-- or manager conflicts, and at least 95% of eligible employees form a pair
-- with one postal code and one country for both parties.

WITH latest_snapshot AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
active_employee_rows AS (
    SELECT
        d.fis_mo_end_dt AS snapshot_date,
        NULLIF(TRIM(d.employee_id), '') AS employee_id,
        NULLIF(TRIM(d.manager_employee_id), '') AS manager_employee_id,
        NULLIF(TRIM(d.postal_code), '') AS postal_code,
        NULLIF(TRIM(d.country), '') AS country,
        d.employee_type
    FROM hrda.post_hire_monthly_worker_dtls d
    JOIN latest_snapshot s
      ON d.fis_mo_end_dt = s.snapshot_date
    WHERE d.worker_type = 'Employee'
      AND d.active_status = 1
      AND NULLIF(TRIM(d.employee_id), '') IS NOT NULL
),
employee_snapshot_state AS (
    SELECT
        snapshot_date,
        employee_id,
        MIN(manager_employee_id) AS selected_manager_employee_id,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT manager_employee_id) AS distinct_manager_id_count,
        COUNT(DISTINCT postal_code) AS distinct_postal_code_count,
        COUNT(DISTINCT country) AS distinct_country_count,
        MAX(CASE WHEN employee_type = 'Regular' THEN 1 ELSE 0 END) AS is_regular_employee
    FROM active_employee_rows
    GROUP BY snapshot_date, employee_id
),
eligible_employee_state AS (
    SELECT
        snapshot_date,
        employee_id,
        selected_manager_employee_id,
        source_row_count,
        distinct_manager_id_count,
        distinct_postal_code_count,
        distinct_country_count
    FROM employee_snapshot_state
    WHERE is_regular_employee = 1
),
pair_reconciliation AS (
    SELECT
        e.snapshot_date,
        e.employee_id,
        e.source_row_count AS employee_source_row_count,
        e.distinct_manager_id_count AS employee_manager_id_count,
        e.distinct_postal_code_count AS employee_postal_code_count,
        e.distinct_country_count AS employee_country_count,
        m.employee_id AS matched_manager_employee_id,
        m.source_row_count AS manager_source_row_count,
        m.distinct_postal_code_count AS manager_postal_code_count,
        m.distinct_country_count AS manager_country_count
    FROM eligible_employee_state e
    LEFT JOIN employee_snapshot_state m
      ON e.snapshot_date = m.snapshot_date
     AND e.selected_manager_employee_id = m.employee_id
     AND e.distinct_manager_id_count = 1
)
SELECT
    snapshot_date,
    COUNT(*) AS eligible_employees,
    SUM(CASE WHEN employee_source_row_count > 1 THEN 1 ELSE 0 END) AS employee_duplicate_source_rows,
    SUM(CASE WHEN employee_manager_id_count > 1 THEN 1 ELSE 0 END) AS employee_manager_conflicts,
    SUM(CASE WHEN employee_country_count = 1 THEN 1 ELSE 0 END) AS employees_with_one_country,
    SUM(CASE WHEN employee_country_count > 1 THEN 1 ELSE 0 END) AS employee_country_conflicts,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL AND manager_country_count = 1 THEN 1 ELSE 0 END) AS matched_managers_with_one_country,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL AND manager_country_count > 1 THEN 1 ELSE 0 END) AS matched_manager_country_conflicts,
    SUM(
        CASE
            WHEN employee_source_row_count = 1
             AND employee_manager_id_count = 1
             AND employee_postal_code_count = 1
             AND employee_country_count = 1
             AND matched_manager_employee_id IS NOT NULL
             AND manager_source_row_count = 1
             AND manager_postal_code_count = 1
             AND manager_country_count = 1
            THEN 1 ELSE 0
        END
    ) AS same_snapshot_residential_geography_pairs
FROM pair_reconciliation
GROUP BY snapshot_date;
