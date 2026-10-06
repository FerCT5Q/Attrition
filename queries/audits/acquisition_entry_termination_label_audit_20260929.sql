-- Auditoría enfocada de la etiqueta de término para Ingreso por adquisición.
-- Motivo de revisión v2: term_type = 'VOLUNTARY' literal devolvió cero.
-- Esta consulta prueba si UPPER(TRIM()) reconoce exclusivamente la etiqueta
-- VOLUNTARY y reconcilia el grain empleado-fecha dentro de la cohorte basal.
-- Sólo devuelve agregados; las claves sólo viven dentro de CTEs.
WITH baseline_population AS (
    SELECT
        CAST(employee_id AS VARCHAR(256)) AS employee_key
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt = DATE '2025-08-24'
    GROUP BY CAST(employee_id AS VARCHAR(256))
),
main_window AS (
    SELECT
        CAST(employee_id AS VARCHAR(256)) AS employee_key,
        term_date,
        NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '') AS term_type_trimmed,
        UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) AS term_type_normalized
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND term_date > DATE '2025-08-24'
      AND term_date <= DATE '2026-08-23'
),
main_normalized_voluntary AS (
    SELECT employee_key, term_date, COUNT(*) AS raw_row_count
    FROM main_window
    WHERE term_type_normalized = 'VOLUNTARY'
    GROUP BY employee_key, term_date
),
all_window AS (
    SELECT
        CAST(employeeid AS VARCHAR(256)) AS employee_key,
        term_date,
        NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '') AS term_type_trimmed,
        UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) AS term_type_normalized
    FROM hrda.all_terminations
    WHERE term_date > DATE '2025-08-24'
      AND term_date <= DATE '2026-08-23'
),
all_normalized_voluntary AS (
    SELECT employee_key, term_date, COUNT(*) AS raw_row_count
    FROM all_window
    WHERE term_type_normalized = 'VOLUNTARY'
    GROUP BY employee_key, term_date
),
main_summary AS (
    SELECT
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT term_type_trimmed) AS trimmed_term_type_count,
        COUNT(DISTINCT term_type_normalized) AS normalized_term_type_count,
        SUM(CASE WHEN term_type_trimmed = 'VOLUNTARY' THEN 1 ELSE 0 END) AS literal_voluntary_row_count,
        SUM(CASE WHEN term_type_normalized = 'VOLUNTARY' THEN 1 ELSE 0 END) AS normalized_voluntary_row_count,
        COUNT(DISTINCT CASE WHEN term_type_normalized = 'VOLUNTARY' THEN employee_key END) AS normalized_voluntary_employee_count,
        SUM(CASE WHEN term_type_trimmed IS NULL THEN 1 ELSE 0 END) AS blank_term_type_row_count
    FROM main_window
),
all_summary AS (
    SELECT
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT term_type_trimmed) AS trimmed_term_type_count,
        COUNT(DISTINCT term_type_normalized) AS normalized_term_type_count,
        SUM(CASE WHEN term_type_trimmed = 'VOLUNTARY' THEN 1 ELSE 0 END) AS literal_voluntary_row_count,
        SUM(CASE WHEN term_type_normalized = 'VOLUNTARY' THEN 1 ELSE 0 END) AS normalized_voluntary_row_count,
        COUNT(DISTINCT CASE WHEN term_type_normalized = 'VOLUNTARY' THEN employee_key END) AS normalized_voluntary_employee_count,
        SUM(CASE WHEN term_type_trimmed IS NULL THEN 1 ELSE 0 END) AS blank_term_type_row_count
    FROM all_window
),
cohort_summary AS (
    SELECT
        COUNT(*) AS baseline_employee_count,
        COUNT(DISTINCT m.employee_key) AS main_normalized_voluntary_cohort_employee_count,
        COUNT(DISTINCT a.employee_key) AS all_normalized_voluntary_cohort_employee_count,
        SUM(CASE WHEN m.raw_row_count > 1 THEN 1 ELSE 0 END) AS main_duplicate_employee_date_event_count,
        SUM(CASE WHEN a.raw_row_count > 1 THEN 1 ELSE 0 END) AS all_duplicate_employee_date_event_count
    FROM baseline_population b
    LEFT JOIN main_normalized_voluntary m
      ON m.employee_key = b.employee_key
    LEFT JOIN all_normalized_voluntary a
      ON a.employee_key = b.employee_key
)
SELECT 'main_source' AS metric_group, 'source_row_count' AS metric_name, source_row_count::DECIMAL(24,6) AS metric_value FROM main_summary
UNION ALL SELECT 'main_source', 'trimmed_term_type_count', trimmed_term_type_count::DECIMAL(24,6) FROM main_summary
UNION ALL SELECT 'main_source', 'normalized_term_type_count', normalized_term_type_count::DECIMAL(24,6) FROM main_summary
UNION ALL SELECT 'main_source', 'literal_voluntary_row_count', literal_voluntary_row_count::DECIMAL(24,6) FROM main_summary
UNION ALL SELECT 'main_source', 'normalized_voluntary_row_count', normalized_voluntary_row_count::DECIMAL(24,6) FROM main_summary
UNION ALL SELECT 'main_source', 'normalized_voluntary_employee_count', normalized_voluntary_employee_count::DECIMAL(24,6) FROM main_summary
UNION ALL SELECT 'main_source', 'blank_term_type_row_count', blank_term_type_row_count::DECIMAL(24,6) FROM main_summary
UNION ALL SELECT 'all_terminations_source', 'source_row_count', source_row_count::DECIMAL(24,6) FROM all_summary
UNION ALL SELECT 'all_terminations_source', 'trimmed_term_type_count', trimmed_term_type_count::DECIMAL(24,6) FROM all_summary
UNION ALL SELECT 'all_terminations_source', 'normalized_term_type_count', normalized_term_type_count::DECIMAL(24,6) FROM all_summary
UNION ALL SELECT 'all_terminations_source', 'literal_voluntary_row_count', literal_voluntary_row_count::DECIMAL(24,6) FROM all_summary
UNION ALL SELECT 'all_terminations_source', 'normalized_voluntary_row_count', normalized_voluntary_row_count::DECIMAL(24,6) FROM all_summary
UNION ALL SELECT 'all_terminations_source', 'normalized_voluntary_employee_count', normalized_voluntary_employee_count::DECIMAL(24,6) FROM all_summary
UNION ALL SELECT 'all_terminations_source', 'blank_term_type_row_count', blank_term_type_row_count::DECIMAL(24,6) FROM all_summary
UNION ALL SELECT 'baseline_cohort', 'baseline_employee_count', baseline_employee_count::DECIMAL(24,6) FROM cohort_summary
UNION ALL SELECT 'baseline_cohort', 'main_normalized_voluntary_cohort_employee_count', main_normalized_voluntary_cohort_employee_count::DECIMAL(24,6) FROM cohort_summary
UNION ALL SELECT 'baseline_cohort', 'all_normalized_voluntary_cohort_employee_count', all_normalized_voluntary_cohort_employee_count::DECIMAL(24,6) FROM cohort_summary
UNION ALL SELECT 'baseline_cohort', 'main_duplicate_employee_date_event_count', main_duplicate_employee_date_event_count::DECIMAL(24,6) FROM cohort_summary
UNION ALL SELECT 'baseline_cohort', 'all_duplicate_employee_date_event_count', all_duplicate_employee_date_event_count::DECIMAL(24,6) FROM cohort_summary
ORDER BY metric_group, metric_name;
