-- Propósito: reconciliar agregadamente el significado de
-- compensation_grade_pa en job_applications_vw.
-- Modo de entrega: presentation; no devuelve identificadores, nombres,
-- correos ni filas individuales.
-- Población: filas de job_applications_vw con al menos un campo de grado.

WITH base AS (
    SELECT
        CASE
            WHEN compensation_grade_pa IS NULL OR TRIM(CAST(compensation_grade_pa AS VARCHAR)) = '' THEN 'missing'
            ELSE 'present'
        END AS pa_status,
        CASE
            WHEN compensation_grade IS NULL OR TRIM(CAST(compensation_grade AS VARCHAR)) = '' THEN 'missing'
            ELSE 'present'
        END AS grade_status,
        CASE
            WHEN rf360_comp_grade IS NULL OR TRIM(CAST(rf360_comp_grade AS VARCHAR)) = '' THEN 'missing'
            ELSE 'present'
        END AS rf360_status,
        CASE
            WHEN job_level_compensation IS NULL OR TRIM(CAST(job_level_compensation AS VARCHAR)) = '' THEN 'missing'
            ELSE 'present'
        END AS job_level_status,
        CASE
            WHEN compensation_grade_pa IS NOT NULL
             AND compensation_grade IS NOT NULL
             AND TRIM(CAST(compensation_grade_pa AS VARCHAR)) = TRIM(CAST(compensation_grade AS VARCHAR))
            THEN 1 ELSE 0
        END AS pa_equals_grade,
        CASE
            WHEN compensation_grade_pa IS NOT NULL
             AND rf360_comp_grade IS NOT NULL
             AND TRIM(CAST(compensation_grade_pa AS VARCHAR)) = TRIM(CAST(rf360_comp_grade AS VARCHAR))
            THEN 1 ELSE 0
        END AS pa_equals_rf360,
        CASE
            WHEN req_id IS NULL OR TRIM(CAST(req_id AS VARCHAR)) = '' THEN 0 ELSE 1
        END AS has_req_id,
        CASE
            WHEN candidate_id IS NULL OR TRIM(CAST(candidate_id AS VARCHAR)) = '' THEN 0 ELSE 1
        END AS has_candidate_id,
        CASE
            WHEN employee_id IS NULL OR TRIM(CAST(employee_id AS VARCHAR)) = '' THEN 0 ELSE 1
        END AS has_employee_id
    FROM hrda.job_applications_vw
), summary AS (
    SELECT
        COUNT(*) AS application_rows,
        SUM(CASE WHEN pa_status = 'present' THEN 1 ELSE 0 END) AS pa_present_rows,
        SUM(CASE WHEN grade_status = 'present' THEN 1 ELSE 0 END) AS compensation_grade_present_rows,
        SUM(CASE WHEN rf360_status = 'present' THEN 1 ELSE 0 END) AS rf360_present_rows,
        SUM(CASE WHEN job_level_status = 'present' THEN 1 ELSE 0 END) AS job_level_compensation_present_rows,
        SUM(CASE WHEN pa_equals_grade = 1 THEN 1 ELSE 0 END) AS pa_equals_compensation_grade_rows,
        SUM(CASE WHEN pa_equals_rf360 = 1 THEN 1 ELSE 0 END) AS pa_equals_rf360_rows,
        SUM(has_req_id) AS rows_with_req_id,
        SUM(has_candidate_id) AS rows_with_candidate_id,
        SUM(has_employee_id) AS rows_with_employee_id
    FROM base
)
SELECT
    application_rows,
    pa_present_rows,
    compensation_grade_present_rows,
    rf360_present_rows,
    job_level_compensation_present_rows,
    pa_equals_compensation_grade_rows,
    pa_equals_rf360_rows,
    rows_with_req_id,
    rows_with_candidate_id,
    rows_with_employee_id,
    pa_present_rows::DECIMAL(18,4) / NULLIF(application_rows, 0) AS pa_coverage,
    pa_equals_compensation_grade_rows::DECIMAL(18,4) / NULLIF(pa_present_rows, 0) AS pa_grade_match_rate,
    pa_equals_rf360_rows::DECIMAL(18,4) / NULLIF(pa_present_rows, 0) AS pa_rf360_match_rate
FROM summary;
