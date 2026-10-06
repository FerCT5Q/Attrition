-- Reconciliación agregada de la cohorte anual usada por la revisión V8.
-- Compara la selección directa de activos Regular con la selección usada por
-- la evidencia congelada de layers. No devuelve identificadores ni filas.
WITH params AS (
    SELECT DATE '2025-08-24' AS baseline_date, DATE '2026-08-23' AS outcome_cutoff
),
direct_target AS (
    SELECT DISTINCT CAST(employee_id AS BIGINT) AS employee_id
    FROM hrda.post_hire_monthly_worker_dtls
    CROSS JOIN params
    WHERE CAST(fis_mo_end_dt AS DATE) = baseline_date
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND employee_id IS NOT NULL
),
layer_style_target AS (
    SELECT CAST(employee_id AS BIGINT) AS employee_id
    FROM hrda.post_hire_monthly_worker_dtls
    CROSS JOIN params
    WHERE CAST(fis_mo_end_dt AS DATE) = baseline_date
      AND active_status = 1
      AND employee_id IS NOT NULL
    GROUP BY 1
    HAVING MAX(CASE WHEN worker_type = 'Employee' AND employee_type = 'Regular' THEN 1 ELSE 0 END) = 1
),
voluntary_events AS (
    SELECT DISTINCT CAST(w.employee_id AS BIGINT) AS employee_id
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN params
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND CAST(w.term_date AS DATE) > baseline_date
      AND CAST(w.term_date AS DATE) <= outcome_cutoff
      AND w.employee_id IS NOT NULL
)
SELECT 'direct_target_count' AS metric, COUNT(*)::BIGINT AS metric_value
FROM direct_target
UNION ALL
SELECT 'layer_style_target_count', COUNT(*)::BIGINT
FROM layer_style_target
UNION ALL
SELECT 'direct_only_target_count', COUNT(*)::BIGINT
FROM (SELECT employee_id FROM direct_target EXCEPT SELECT employee_id FROM layer_style_target) AS d
UNION ALL
SELECT 'layer_style_only_target_count', COUNT(*)::BIGINT
FROM (SELECT employee_id FROM layer_style_target EXCEPT SELECT employee_id FROM direct_target) AS d
UNION ALL
SELECT 'direct_target_voluntary_exit_count', COUNT(*)::BIGINT
FROM direct_target AS d
INNER JOIN voluntary_events AS v ON v.employee_id = d.employee_id
UNION ALL
SELECT 'layer_style_target_voluntary_exit_count', COUNT(*)::BIGINT
FROM layer_style_target AS d
INNER JOIN voluntary_events AS v ON v.employee_id = d.employee_id
ORDER BY metric;
