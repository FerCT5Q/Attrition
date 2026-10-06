-- Hours away from manager: HRDA component and same-snapshot join audit.
--
-- Claim tested: HRDA can form an unambiguous, time-aligned employee-manager
-- pair with a stored office_site for each side at the 2026-08-23 monthly
-- snapshot. This audit does NOT calculate travel time or time-zone distance.
--
-- Population: active Employee / Regular employees at the 2026-08-23
-- hrda.post_hire_monthly_worker_dtls snapshot. Manager candidates are
-- active employees at that same snapshot, regardless of employee_type.
-- Grain: one employee-manager pair, with employee identifiers retained only
-- inside CTEs and never returned.
--
-- Acceptance rule for the internal-pair component only: at least 30 eligible
-- employees, zero employee duplicate source rows, zero conflicting manager
-- assignments, zero employees without a manager, zero unmatched managers, and
-- one stored office_site for both parties in every eligible pair. A passing
-- internal join cannot validate the feature definition without an approved,
-- effective-dated site-to-travel/time-zone reference and its business rules.

WITH latest_snapshot AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
active_employee_rows AS (
    SELECT
        d.fis_mo_end_dt AS snapshot_date,
        NULLIF(TRIM(d.employee_id), '') AS employee_id,
        NULLIF(TRIM(d.manager_employee_id), '') AS manager_employee_id,
        NULLIF(UPPER(TRIM(d.office_site)), '') AS office_site_normalized,
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
        COUNT(DISTINCT office_site_normalized) AS distinct_office_site_count,
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
        distinct_office_site_count,
        is_regular_employee
    FROM employee_snapshot_state
    WHERE is_regular_employee = 1
),
pair_reconciliation AS (
    SELECT
        e.snapshot_date,
        e.employee_id,
        e.source_row_count AS employee_source_row_count,
        e.distinct_manager_id_count AS employee_manager_id_count,
        e.distinct_office_site_count AS employee_office_site_count,
        m.employee_id AS matched_manager_employee_id,
        m.source_row_count AS manager_source_row_count,
        m.distinct_office_site_count AS manager_office_site_count
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
    SUM(CASE WHEN employee_manager_id_count = 0 THEN 1 ELSE 0 END) AS employees_without_manager,
    SUM(CASE WHEN employee_office_site_count > 1 THEN 1 ELSE 0 END) AS employee_office_site_conflicts,
    SUM(CASE WHEN employee_office_site_count = 0 THEN 1 ELSE 0 END) AS employees_without_office_site,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_managers,
    SUM(CASE WHEN employee_manager_id_count = 1 AND matched_manager_employee_id IS NULL THEN 1 ELSE 0 END) AS unmatched_managers,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL AND manager_source_row_count > 1 THEN 1 ELSE 0 END) AS matched_manager_duplicate_source_rows,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL AND manager_office_site_count > 1 THEN 1 ELSE 0 END) AS matched_manager_office_site_conflicts,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL AND manager_office_site_count = 0 THEN 1 ELSE 0 END) AS matched_managers_without_office_site,
    SUM(
        CASE
            WHEN employee_source_row_count = 1
             AND employee_manager_id_count = 1
             AND employee_office_site_count = 1
             AND matched_manager_employee_id IS NOT NULL
             AND manager_source_row_count = 1
             AND manager_office_site_count = 1
            THEN 1 ELSE 0
        END
    ) AS internally_unambiguous_site_pairs
FROM pair_reconciliation
GROUP BY snapshot_date;
