-- Propósito: comprobar si compensation_grade_pa de la aplicación coincide
-- con el grado almacenado para la requisición asociada.
-- Modo de entrega: presentation; resultados agregados solamente.

WITH requisition_by_key AS (
    SELECT
        NULLIF(TRIM(CAST(req_id AS VARCHAR)), '') AS req_key,
        COUNT(*) AS requisition_rows,
        COUNT(DISTINCT NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '')) AS req_grade_value_count,
        COUNT(DISTINCT NULLIF(TRIM(CAST(rf360_comp_grade AS VARCHAR)), '')) AS req_rf360_value_count,
        COUNT(DISTINCT NULLIF(TRIM(CAST(requisition_compensation_grade_profile AS VARCHAR)), '') ) AS req_profile_value_count,
        MAX(NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '')) AS req_compensation_grade,
        MAX(NULLIF(TRIM(CAST(rf360_comp_grade AS VARCHAR)), '')) AS req_rf360_comp_grade,
        MAX(NULLIF(TRIM(CAST(requisition_compensation_grade_profile AS VARCHAR)), '')) AS req_compensation_grade_profile
    FROM hrda.requisitions
    WHERE NULLIF(TRIM(CAST(req_id AS VARCHAR)), '') IS NOT NULL
    GROUP BY 1
), application_rows AS (
    SELECT
        NULLIF(TRIM(CAST(a.req_id AS VARCHAR)), '') AS req_key,
        NULLIF(TRIM(CAST(a.compensation_grade_pa AS VARCHAR)), '') AS pa_grade,
        NULLIF(TRIM(CAST(a.compensation_grade AS VARCHAR)), '') AS application_grade,
        NULLIF(TRIM(CAST(a.job_level_compensation AS VARCHAR)), '') AS application_job_level,
        NULLIF(TRIM(CAST(a.rf360_comp_grade AS VARCHAR)), '') AS application_rf360
    FROM hrda.job_applications_vw a
), joined AS (
    SELECT
        a.req_key,
        a.pa_grade,
        a.application_grade,
        a.application_job_level,
        a.application_rf360,
        r.requisition_rows,
        r.req_grade_value_count,
        r.req_rf360_value_count,
        r.req_profile_value_count,
        r.req_compensation_grade,
        r.req_rf360_comp_grade,
        r.req_compensation_grade_profile
    FROM application_rows a
    LEFT JOIN requisition_by_key r
      ON a.req_key = r.req_key
), summary AS (
    SELECT
        COUNT(*) AS application_rows,
        SUM(CASE WHEN req_key IS NOT NULL THEN 1 ELSE 0 END) AS rows_with_req_key,
        SUM(CASE WHEN requisition_rows IS NOT NULL THEN 1 ELSE 0 END) AS rows_matching_a_requisition,
        SUM(CASE WHEN requisition_rows IS NOT NULL AND req_grade_value_count = 1 THEN 1 ELSE 0 END) AS rows_with_unambiguous_requisition_grade,
        SUM(CASE WHEN requisition_rows IS NOT NULL AND req_rf360_value_count = 1 THEN 1 ELSE 0 END) AS rows_with_unambiguous_requisition_rf360,
        SUM(CASE WHEN requisition_rows IS NOT NULL AND req_profile_value_count = 1 THEN 1 ELSE 0 END) AS rows_with_unambiguous_requisition_profile,
        SUM(CASE WHEN requisition_rows IS NOT NULL AND req_grade_value_count = 1 AND pa_grade IS NOT NULL AND pa_grade = req_compensation_grade THEN 1 ELSE 0 END) AS pa_matches_requisition_grade,
        SUM(CASE WHEN requisition_rows IS NOT NULL AND req_grade_value_count = 1 AND application_grade IS NOT NULL AND application_grade = req_compensation_grade THEN 1 ELSE 0 END) AS application_grade_matches_requisition_grade,
        SUM(CASE WHEN requisition_rows IS NOT NULL AND req_grade_value_count = 1 AND application_job_level IS NOT NULL AND application_job_level = req_compensation_grade THEN 1 ELSE 0 END) AS job_level_matches_requisition_grade,
        SUM(CASE WHEN requisition_rows IS NOT NULL AND req_rf360_value_count = 1 AND pa_grade IS NOT NULL AND pa_grade = req_rf360_comp_grade THEN 1 ELSE 0 END) AS pa_matches_requisition_rf360,
        SUM(CASE WHEN requisition_rows IS NOT NULL AND req_profile_value_count = 1 AND pa_grade IS NOT NULL AND pa_grade = req_compensation_grade_profile THEN 1 ELSE 0 END) AS pa_matches_requisition_profile
    FROM joined
)
SELECT
    application_rows,
    rows_with_req_key,
    rows_matching_a_requisition,
    rows_with_unambiguous_requisition_grade,
    rows_with_unambiguous_requisition_rf360,
    rows_with_unambiguous_requisition_profile,
    pa_matches_requisition_grade,
    application_grade_matches_requisition_grade,
    job_level_matches_requisition_grade,
    pa_matches_requisition_rf360,
    pa_matches_requisition_profile,
    rows_matching_a_requisition::DECIMAL(18,4) / NULLIF(rows_with_req_key, 0) AS requisition_match_rate,
    pa_matches_requisition_grade::DECIMAL(18,4) / NULLIF(rows_with_unambiguous_requisition_grade, 0) AS pa_requisition_grade_match_rate,
    application_grade_matches_requisition_grade::DECIMAL(18,4) / NULLIF(rows_with_unambiguous_requisition_grade, 0) AS application_grade_requisition_grade_match_rate,
    job_level_matches_requisition_grade::DECIMAL(18,4) / NULLIF(rows_with_unambiguous_requisition_grade, 0) AS job_level_requisition_grade_match_rate,
    pa_matches_requisition_rf360::DECIMAL(18,4) / NULLIF(rows_with_unambiguous_requisition_rf360, 0) AS pa_requisition_rf360_match_rate,
    pa_matches_requisition_profile::DECIMAL(18,4) / NULLIF(rows_with_unambiguous_requisition_profile, 0) AS pa_requisition_profile_match_rate
FROM summary;
