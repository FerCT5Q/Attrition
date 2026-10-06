-- Manager-employee residential postal-pair availability audit.
--
-- Claim tested: a same-snapshot employee-manager pair has one stored
-- postal_code for each party. This is a technical availability audit only;
-- it does not return postal codes, addresses, employee IDs, or distances.
--
-- Proposed concept if governance approves it: approximate geographic
-- separation between the residential postal centroids of an employee and
-- their active manager. It is NOT office-to-office distance, travel time,
-- time-zone separation, or a measure of "hours away".
--
-- Population: active Employee / Regular employees at the 2026-08-23 monthly
-- snapshot. Manager candidates are active employees at that same snapshot,
-- regardless of employee_type. Grain: one employee-manager pair.
--
-- Technical acceptance rule: at least 30 eligible employees; no duplicate
-- source rows or conflicting manager IDs; and at least 95% of eligible
-- employees have one postal_code for both parties after the same-snapshot
-- manager join. Privacy, Legal, source-owner, bias, and historical
-- availability approval are separate required gates.

WITH latest_snapshot AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
active_employee_rows AS (
    SELECT
        d.fis_mo_end_dt AS snapshot_date,
        NULLIF(TRIM(d.employee_id), '') AS employee_id,
        NULLIF(TRIM(d.manager_employee_id), '') AS manager_employee_id,
        NULLIF(TRIM(d.postal_code), '') AS postal_code,
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
        MIN(postal_code) AS selected_postal_code,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT manager_employee_id) AS distinct_manager_id_count,
        COUNT(DISTINCT postal_code) AS distinct_postal_code_count,
        MAX(CASE WHEN employee_type = 'Regular' THEN 1 ELSE 0 END) AS is_regular_employee
    FROM active_employee_rows
    GROUP BY snapshot_date, employee_id
),
eligible_employee_state AS (
    SELECT
        snapshot_date,
        employee_id,
        selected_manager_employee_id,
        selected_postal_code,
        source_row_count,
        distinct_manager_id_count,
        distinct_postal_code_count
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
        e.selected_postal_code AS employee_postal_code,
        m.employee_id AS matched_manager_employee_id,
        m.source_row_count AS manager_source_row_count,
        m.distinct_postal_code_count AS manager_postal_code_count,
        m.selected_postal_code AS manager_postal_code
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
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_managers,
    SUM(CASE WHEN employee_manager_id_count = 1 AND matched_manager_employee_id IS NULL THEN 1 ELSE 0 END) AS unmatched_managers,
    SUM(CASE WHEN employee_postal_code_count = 1 THEN 1 ELSE 0 END) AS employees_with_one_postal_code,
    SUM(CASE WHEN employee_postal_code_count > 1 THEN 1 ELSE 0 END) AS employee_postal_code_conflicts,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL AND manager_postal_code_count = 1 THEN 1 ELSE 0 END) AS matched_managers_with_one_postal_code,
    SUM(CASE WHEN matched_manager_employee_id IS NOT NULL AND manager_postal_code_count > 1 THEN 1 ELSE 0 END) AS matched_manager_postal_code_conflicts,
    SUM(
        CASE
            WHEN employee_source_row_count = 1
             AND employee_manager_id_count = 1
             AND employee_postal_code_count = 1
             AND matched_manager_employee_id IS NOT NULL
             AND manager_source_row_count = 1
             AND manager_postal_code_count = 1
            THEN 1 ELSE 0
        END
    ) AS same_snapshot_residential_postal_pairs,
    SUM(
        CASE
            WHEN employee_source_row_count = 1
             AND employee_manager_id_count = 1
             AND employee_postal_code_count = 1
             AND matched_manager_employee_id IS NOT NULL
             AND manager_source_row_count = 1
             AND manager_postal_code_count = 1
             AND employee_postal_code = manager_postal_code
            THEN 1 ELSE 0
        END
    ) AS same_residential_postal_pairs
FROM pair_reconciliation
GROUP BY snapshot_date;
