-- Propósito: perfilar las ramas UNION ALL que construyen
-- job_applications_vw y la cobertura de compensation_grade_pa.
-- Modo de entrega: presentation; sólo conteos agregados.

WITH branch_profile AS (
    SELECT
        'applications_passthrough' AS view_branch,
        COUNT(*) AS rows_in_branch,
        SUM(CASE WHEN compensation_grade_pa IS NOT NULL AND TRIM(CAST(compensation_grade_pa AS VARCHAR)) <> '' THEN 1 ELSE 0 END) AS pa_present_rows
    FROM hrda.applications

    UNION ALL

    SELECT
        'job_applications_without_requisition' AS view_branch,
        COUNT(*) AS rows_in_branch,
        CAST(0 AS BIGINT) AS pa_present_rows
    FROM hrda.job_applications
    WHERE application_date > '2024-10-29'::DATE
      AND requisition_id IS NULL

    UNION ALL

    SELECT
        'job_applications_with_requisition' AS view_branch,
        COUNT(*) AS rows_in_branch,
        SUM(CASE WHEN r.compensation_grade IS NOT NULL AND TRIM(CAST(r.compensation_grade AS VARCHAR)) <> '' THEN 1 ELSE 0 END) AS pa_present_rows
    FROM hrda.job_applications ja
    LEFT JOIN hrda.requisitions r
      ON CAST(ja.requisition_id AS VARCHAR) = CAST(r.req_id AS VARCHAR)
    WHERE ja.application_date > '2024-10-29'::DATE
      AND r.last_modified_date = (
          SELECT MAX(rd.last_modified_date)
          FROM hrda.requisitions rd
          WHERE CAST(rd.req_id AS VARCHAR) = CAST(r.req_id AS VARCHAR)
            AND rd.last_modified_date <= ja.last_modified_date
      )
)
SELECT
    view_branch,
    rows_in_branch,
    pa_present_rows,
    pa_present_rows::DECIMAL(18,4) / NULLIF(rows_in_branch, 0) AS pa_coverage
FROM branch_profile
ORDER BY view_branch;
