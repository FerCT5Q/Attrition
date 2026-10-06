-- Auditoría v3 de grain de término para Ingreso por adquisición.
-- La tabla mensual repite eventos en snapshots posteriores. Esta consulta
-- separa repetición de filas fuente, múltiples fechas de término por persona y
-- el evento seleccionado para la tasa (MIN(term_date), una persona una vez).
-- Sólo devuelve métricas agregadas.
WITH baseline_population AS (
    SELECT CAST(employee_id AS VARCHAR(256)) AS employee_key
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt = DATE '2025-08-24'
    GROUP BY CAST(employee_id AS VARCHAR(256))
),
main_source_rows AS (
    SELECT
        CAST(employee_id AS VARCHAR(256)) AS employee_key,
        term_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date > DATE '2025-08-24'
      AND term_date <= DATE '2026-08-23'
),
main_employee_date AS (
    SELECT employee_key, term_date, COUNT(*) AS source_row_count
    FROM main_source_rows
    GROUP BY employee_key, term_date
),
main_employee AS (
    SELECT
        employee_key,
        MIN(term_date) AS selected_term_date,
        COUNT(*) AS distinct_term_date_count,
        SUM(source_row_count) AS source_row_count
    FROM main_employee_date
    GROUP BY employee_key
),
all_source_rows AS (
    SELECT
        CAST(employeeid AS VARCHAR(256)) AS employee_key,
        term_date
    FROM hrda.all_terminations
    WHERE UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date > DATE '2025-08-24'
      AND term_date <= DATE '2026-08-23'
),
all_employee_date AS (
    SELECT employee_key, term_date, COUNT(*) AS source_row_count
    FROM all_source_rows
    GROUP BY employee_key, term_date
),
all_employee AS (
    SELECT
        employee_key,
        MIN(term_date) AS selected_term_date,
        COUNT(*) AS distinct_term_date_count,
        SUM(source_row_count) AS source_row_count
    FROM all_employee_date
    GROUP BY employee_key
),
baseline_main AS (
    SELECT
        m.employee_key,
        m.selected_term_date,
        m.distinct_term_date_count,
        m.source_row_count
    FROM baseline_population b
    INNER JOIN main_employee m
      ON m.employee_key = b.employee_key
),
baseline_all AS (
    SELECT
        a.employee_key,
        a.selected_term_date,
        a.distinct_term_date_count,
        a.source_row_count
    FROM baseline_population b
    INNER JOIN all_employee a
      ON a.employee_key = b.employee_key
),
main_metrics AS (
    SELECT
        COUNT(*) AS source_selected_employee_count,
        SUM(source_row_count) AS source_row_count,
        SUM(distinct_term_date_count) AS source_employee_date_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS source_repeated_employee_count,
        SUM(CASE WHEN distinct_term_date_count > 1 THEN 1 ELSE 0 END) AS source_multi_date_employee_count
    FROM main_employee
),
all_metrics AS (
    SELECT
        COUNT(*) AS source_selected_employee_count,
        SUM(source_row_count) AS source_row_count,
        SUM(distinct_term_date_count) AS source_employee_date_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS source_repeated_employee_count,
        SUM(CASE WHEN distinct_term_date_count > 1 THEN 1 ELSE 0 END) AS source_multi_date_employee_count
    FROM all_employee
),
cohort_metrics AS (
    SELECT
        (SELECT COUNT(*) FROM baseline_population) AS baseline_employee_count,
        (SELECT COUNT(*) FROM baseline_main) AS main_selected_cohort_exit_count,
        (SELECT COUNT(*) FROM baseline_all) AS all_selected_cohort_exit_count,
        (SELECT SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) FROM baseline_main) AS main_repeated_source_row_cohort_employee_count,
        (SELECT SUM(CASE WHEN distinct_term_date_count > 1 THEN 1 ELSE 0 END) FROM baseline_main) AS main_multi_date_cohort_employee_count,
        (SELECT SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) FROM baseline_all) AS all_repeated_source_row_cohort_employee_count,
        (SELECT SUM(CASE WHEN distinct_term_date_count > 1 THEN 1 ELSE 0 END) FROM baseline_all) AS all_multi_date_cohort_employee_count
),
source_comparison AS (
    SELECT
        SUM(CASE WHEN m.employee_key IS NOT NULL THEN 1 ELSE 0 END) AS main_selected_cohort_exit_count,
        SUM(CASE WHEN a.employee_key IS NOT NULL THEN 1 ELSE 0 END) AS all_selected_cohort_exit_count,
        SUM(CASE WHEN m.employee_key IS NOT NULL AND a.employee_key IS NOT NULL AND m.selected_term_date = a.selected_term_date THEN 1 ELSE 0 END) AS matching_employee_date_count,
        SUM(CASE WHEN m.employee_key IS NOT NULL AND (a.employee_key IS NULL OR m.selected_term_date <> a.selected_term_date) THEN 1 ELSE 0 END) AS main_only_or_date_mismatch_count,
        SUM(CASE WHEN a.employee_key IS NOT NULL AND (m.employee_key IS NULL OR a.selected_term_date <> m.selected_term_date) THEN 1 ELSE 0 END) AS all_only_or_date_mismatch_count
    FROM baseline_main m
    FULL OUTER JOIN baseline_all a
      ON a.employee_key = m.employee_key
)
SELECT 'main_source' AS metric_group, 'source_selected_employee_count' AS metric_name, source_selected_employee_count::DECIMAL(24,6) AS metric_value FROM main_metrics
UNION ALL SELECT 'main_source', 'source_row_count', source_row_count::DECIMAL(24,6) FROM main_metrics
UNION ALL SELECT 'main_source', 'source_employee_date_count', source_employee_date_count::DECIMAL(24,6) FROM main_metrics
UNION ALL SELECT 'main_source', 'source_repeated_employee_count', source_repeated_employee_count::DECIMAL(24,6) FROM main_metrics
UNION ALL SELECT 'main_source', 'source_multi_date_employee_count', source_multi_date_employee_count::DECIMAL(24,6) FROM main_metrics
UNION ALL SELECT 'all_terminations_source', 'source_selected_employee_count', source_selected_employee_count::DECIMAL(24,6) FROM all_metrics
UNION ALL SELECT 'all_terminations_source', 'source_row_count', source_row_count::DECIMAL(24,6) FROM all_metrics
UNION ALL SELECT 'all_terminations_source', 'source_employee_date_count', source_employee_date_count::DECIMAL(24,6) FROM all_metrics
UNION ALL SELECT 'all_terminations_source', 'source_repeated_employee_count', source_repeated_employee_count::DECIMAL(24,6) FROM all_metrics
UNION ALL SELECT 'all_terminations_source', 'source_multi_date_employee_count', source_multi_date_employee_count::DECIMAL(24,6) FROM all_metrics
UNION ALL SELECT 'baseline_cohort', 'baseline_employee_count', baseline_employee_count::DECIMAL(24,6) FROM cohort_metrics
UNION ALL SELECT 'baseline_cohort', 'main_selected_cohort_exit_count', main_selected_cohort_exit_count::DECIMAL(24,6) FROM cohort_metrics
UNION ALL SELECT 'baseline_cohort', 'all_selected_cohort_exit_count', all_selected_cohort_exit_count::DECIMAL(24,6) FROM cohort_metrics
UNION ALL SELECT 'baseline_cohort', 'main_repeated_source_row_cohort_employee_count', main_repeated_source_row_cohort_employee_count::DECIMAL(24,6) FROM cohort_metrics
UNION ALL SELECT 'baseline_cohort', 'main_multi_date_cohort_employee_count', main_multi_date_cohort_employee_count::DECIMAL(24,6) FROM cohort_metrics
UNION ALL SELECT 'baseline_cohort', 'all_repeated_source_row_cohort_employee_count', all_repeated_source_row_cohort_employee_count::DECIMAL(24,6) FROM cohort_metrics
UNION ALL SELECT 'baseline_cohort', 'all_multi_date_cohort_employee_count', all_multi_date_cohort_employee_count::DECIMAL(24,6) FROM cohort_metrics
UNION ALL SELECT 'source_comparison', 'main_selected_cohort_exit_count', main_selected_cohort_exit_count::DECIMAL(24,6) FROM source_comparison
UNION ALL SELECT 'source_comparison', 'all_selected_cohort_exit_count', all_selected_cohort_exit_count::DECIMAL(24,6) FROM source_comparison
UNION ALL SELECT 'source_comparison', 'matching_employee_date_count', matching_employee_date_count::DECIMAL(24,6) FROM source_comparison
UNION ALL SELECT 'source_comparison', 'main_only_or_date_mismatch_count', main_only_or_date_mismatch_count::DECIMAL(24,6) FROM source_comparison
UNION ALL SELECT 'source_comparison', 'all_only_or_date_mismatch_count', all_only_or_date_mismatch_count::DECIMAL(24,6) FROM source_comparison
ORDER BY metric_group, metric_name;
