-- Residential distance from manager: fixed-snapshot eligibility reconciliation.
--
-- Claim tested: at the 2026-08-23 monthly snapshot, an active regular
-- employee can be paired with exactly one active same-snapshot manager and
-- each selected party has exactly one stored postal-code proxy and country.
--
-- The query is aggregate-only. Employee IDs, manager IDs, postal codes,
-- addresses, country labels, hashes, and calculated distances stay inside
-- CTEs and are not returned.
--
-- Acceptance rule: at least 30 active regular employees; zero duplicate or
-- conflicting selected rows; feature_eligible_pairs + key_unavailable_employees
-- equals the active regular workforce; and all feature-eligible pairs meet the
-- one-manager / one-postal / one-country same-snapshot condition. Centroid
-- matching and distance-band reconciliation are validated separately by the
-- frozen local evidence builder.

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
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT manager_employee_id) AS manager_id_count,
        COUNT(DISTINCT postal_code) AS postal_code_count,
        COUNT(DISTINCT country) AS country_count,
        MAX(CASE WHEN employee_type = 'Regular' THEN 1 ELSE 0 END) AS is_regular_employee
    FROM active_employee_rows
    GROUP BY snapshot_date, employee_id
),
regular_employee_state AS (
    SELECT
        snapshot_date,
        employee_id,
        selected_manager_employee_id,
        source_row_count,
        manager_id_count,
        postal_code_count,
        country_count
    FROM employee_snapshot_state
    WHERE is_regular_employee = 1
),
pair_reconciliation AS (
    SELECT
        e.snapshot_date,
        e.source_row_count AS employee_source_row_count,
        e.manager_id_count AS employee_manager_id_count,
        e.postal_code_count AS employee_postal_code_count,
        e.country_count AS employee_country_count,
        m.employee_id AS matched_manager_employee_id,
        m.source_row_count AS manager_source_row_count,
        m.postal_code_count AS manager_postal_code_count,
        m.country_count AS manager_country_count
    FROM regular_employee_state e
    LEFT JOIN employee_snapshot_state m
      ON e.snapshot_date = m.snapshot_date
     AND e.selected_manager_employee_id = m.employee_id
     AND e.manager_id_count = 1
)
SELECT
    snapshot_date,
    COUNT(*) AS active_regular_employees,
    SUM(CASE WHEN employee_source_row_count > 1 THEN 1 ELSE 0 END) AS employee_duplicate_source_rows,
    SUM(CASE WHEN employee_manager_id_count > 1 THEN 1 ELSE 0 END) AS employee_manager_conflicts,
    SUM(CASE WHEN employee_manager_id_count <> 1 THEN 1 ELSE 0 END) AS employees_without_one_manager,
    SUM(CASE WHEN employee_postal_code_count > 1 THEN 1 ELSE 0 END) AS employee_postal_code_conflicts,
    SUM(CASE WHEN employee_country_count > 1 THEN 1 ELSE 0 END) AS employee_country_conflicts,
    SUM(CASE WHEN employee_manager_id_count = 1 AND matched_manager_employee_id IS NULL THEN 1 ELSE 0 END) AS unmatched_managers,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL AND manager_source_row_count > 1 THEN 1 ELSE 0 END) AS manager_duplicate_source_rows,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL AND manager_postal_code_count > 1 THEN 1 ELSE 0 END) AS manager_postal_code_conflicts,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL AND manager_country_count > 1 THEN 1 ELSE 0 END) AS manager_country_conflicts,
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
    ) AS feature_eligible_pairs,
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
            THEN 0 ELSE 1
        END
    ) AS key_unavailable_employees
FROM pair_reconciliation
GROUP BY snapshot_date;
