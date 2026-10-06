-- Propósito: mapear los tres títulos exactos de aplicación al grade de la
-- posición en México; no devuelve candidatos ni identificadores.
-- Modo de entrega: presentation.

SELECT
    CASE
        WHEN LOWER(COALESCE(job_posting_title, '')) LIKE '%database administrator%'
            THEN 'database_administrator'
        WHEN LOWER(COALESCE(job_posting_title, '')) = 'cyber security engineer, senior'
            THEN 'cyber_security_engineer_senior'
        WHEN LOWER(COALESCE(job_posting_title, '')) = 'software developer, senior'
            THEN 'software_developer_senior'
        WHEN LOWER(COALESCE(job_posting_title, '')) LIKE '%senior cyber security engineer%'
            THEN 'senior_cyber_security_engineer_variant'
    END AS requested_role,
    job_posting_title,
    primary_location,
    country_of_job_requisition,
    compensation_grade_pa,
    COUNT(*) AS application_rows
FROM hrda.job_applications_vw
WHERE LOWER(COALESCE(country_of_job_requisition, '')) = 'mexico'
  AND (
      LOWER(COALESCE(job_posting_title, '')) LIKE '%database administrator%'
      OR LOWER(COALESCE(job_posting_title, '')) = 'cyber security engineer, senior'
      OR LOWER(COALESCE(job_posting_title, '')) = 'software developer, senior'
      OR LOWER(COALESCE(job_posting_title, '')) LIKE '%senior cyber security engineer%'
  )
GROUP BY 1, 2, 3, 4, 5
ORDER BY requested_role, application_rows DESC;
