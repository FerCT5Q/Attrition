-- Auditoría v4 de pertenencia basal versus filtros del registro posterior.
-- La cohorte es Active Regular Employee al 2025-08-24. El outcome se define
-- por una salida Voluntary posterior de esa misma persona; no se reclasifica
-- por worker_type/employee_type de una fila posterior de término. Sólo agrega.
WITH baseline_population AS (
    SELECT CAST(employee_id AS VARCHAR(256)) AS employee_key
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt = DATE '2025-08-24'
    GROUP BY CAST(employee_id AS VARCHAR(256))
),
voluntary_outcome_rows AS (
    SELECT
        CAST(employee_id AS VARCHAR(256)) AS employee_key,
        term_date,
        CASE
            WHEN worker_type = 'Employee' AND employee_type = 'Regular' THEN 1
            ELSE 0
        END AS post_snapshot_employee_regular_flag
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date > DATE '2025-08-24'
      AND term_date <= DATE '2026-08-23'
),
voluntary_outcome_by_person AS (
    SELECT
        employee_key,
        MIN(term_date) AS selected_term_date,
        MAX(post_snapshot_employee_regular_flag) AS has_employee_regular_source_row,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT term_date) AS distinct_term_date_count
    FROM voluntary_outcome_rows
    GROUP BY employee_key
),
baseline_outcomes AS (
    SELECT
        b.employee_key,
        o.selected_term_date,
        o.has_employee_regular_source_row,
        o.source_row_count,
        o.distinct_term_date_count
    FROM baseline_population b
    LEFT JOIN voluntary_outcome_by_person o
      ON o.employee_key = b.employee_key
),
metrics AS (
    SELECT
        COUNT(*) AS baseline_employee_count,
        SUM(CASE WHEN selected_term_date IS NOT NULL THEN 1 ELSE 0 END) AS baseline_membership_only_exit_count,
        SUM(CASE WHEN selected_term_date IS NOT NULL AND has_employee_regular_source_row = 1 THEN 1 ELSE 0 END) AS outcome_row_employee_regular_exit_count,
        SUM(CASE WHEN selected_term_date IS NOT NULL AND has_employee_regular_source_row = 0 THEN 1 ELSE 0 END) AS excluded_by_post_snapshot_classification_count,
        SUM(CASE WHEN selected_term_date IS NOT NULL AND distinct_term_date_count > 1 THEN 1 ELSE 0 END) AS multi_date_exit_person_count,
        SUM(CASE WHEN selected_term_date IS NOT NULL AND source_row_count > 1 THEN 1 ELSE 0 END) AS repeated_source_row_exit_person_count
    FROM baseline_outcomes
)
SELECT 'baseline_membership' AS metric_group, 'baseline_employee_count' AS metric_name, baseline_employee_count::DECIMAL(24,6) AS metric_value FROM metrics
UNION ALL SELECT 'baseline_membership', 'baseline_membership_only_exit_count', baseline_membership_only_exit_count::DECIMAL(24,6) FROM metrics
UNION ALL SELECT 'baseline_membership', 'outcome_row_employee_regular_exit_count', outcome_row_employee_regular_exit_count::DECIMAL(24,6) FROM metrics
UNION ALL SELECT 'baseline_membership', 'excluded_by_post_snapshot_classification_count', excluded_by_post_snapshot_classification_count::DECIMAL(24,6) FROM metrics
UNION ALL SELECT 'baseline_membership', 'multi_date_exit_person_count', multi_date_exit_person_count::DECIMAL(24,6) FROM metrics
UNION ALL SELECT 'baseline_membership', 'repeated_source_row_exit_person_count', repeated_source_row_exit_person_count::DECIMAL(24,6) FROM metrics
ORDER BY metric_name;
