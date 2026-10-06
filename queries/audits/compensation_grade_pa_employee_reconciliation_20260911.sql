-- Propósito: contrastar compensation_grade_pa de la aplicación con el
-- compensation_grade del empleado en worker_details_latest.
-- Esto es una comprobación contextual; no devuelve identificadores ni filas.
-- Modo de entrega: presentation.

WITH worker_by_employee AS (
    SELECT
        CAST(employee_id AS VARCHAR) AS employee_key,
        COUNT(*) AS worker_rows,
        COUNT(DISTINCT NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '')) AS worker_grade_value_count,
        MAX(NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '')) AS worker_compensation_grade
    FROM hrda.worker_details_latest
    WHERE employee_id IS NOT NULL
    GROUP BY 1
), application_rows AS (
    SELECT
        CAST(a.employee_id AS VARCHAR) AS employee_key,
        NULLIF(TRIM(CAST(a.compensation_grade_pa AS VARCHAR)), '') AS pa_grade,
        NULLIF(TRIM(CAST(a.compensation_grade AS VARCHAR)), '') AS application_grade
    FROM hrda.job_applications_vw a
    WHERE a.employee_id IS NOT NULL
), joined AS (
    SELECT
        a.pa_grade,
        a.application_grade,
        w.worker_rows,
        w.worker_grade_value_count,
        w.worker_compensation_grade
    FROM application_rows a
    LEFT JOIN worker_by_employee w
      ON a.employee_key = w.employee_key
), summary AS (
    SELECT
        COUNT(*) AS application_rows_with_employee_id,
        SUM(CASE WHEN worker_rows IS NOT NULL THEN 1 ELSE 0 END) AS rows_matching_worker_latest,
        SUM(CASE WHEN worker_rows IS NOT NULL AND worker_grade_value_count = 1 THEN 1 ELSE 0 END) AS rows_with_unambiguous_worker_grade,
        SUM(CASE WHEN worker_rows IS NOT NULL AND worker_grade_value_count = 1 AND pa_grade IS NOT NULL AND pa_grade = worker_compensation_grade THEN 1 ELSE 0 END) AS pa_matches_worker_grade,
        SUM(CASE WHEN worker_rows IS NOT NULL AND worker_grade_value_count = 1 AND application_grade IS NOT NULL AND application_grade = worker_compensation_grade THEN 1 ELSE 0 END) AS application_grade_matches_worker_grade
    FROM joined
)
SELECT
    application_rows_with_employee_id,
    rows_matching_worker_latest,
    rows_with_unambiguous_worker_grade,
    pa_matches_worker_grade,
    application_grade_matches_worker_grade,
    rows_matching_worker_latest::DECIMAL(18,4) / NULLIF(application_rows_with_employee_id, 0) AS worker_match_rate,
    pa_matches_worker_grade::DECIMAL(18,4) / NULLIF(rows_with_unambiguous_worker_grade, 0) AS pa_worker_grade_match_rate,
    application_grade_matches_worker_grade::DECIMAL(18,4) / NULLIF(rows_with_unambiguous_worker_grade, 0) AS application_grade_worker_grade_match_rate
FROM summary;
