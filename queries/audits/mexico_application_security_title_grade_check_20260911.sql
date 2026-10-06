-- Propósito: revisar variantes del título en aplicaciones y el grade de
-- posición que trae la aplicación; resultados agregados.
-- Modo de entrega: presentation; no devuelve candidatos ni IDs.

SELECT
    job_posting_title,
    primary_location,
    country_of_job_requisition,
    compensation_grade_pa,
    COUNT(*) AS application_rows
FROM hrda.job_applications_vw
WHERE LOWER(COALESCE(country_of_job_requisition, '')) LIKE '%mex%'
  AND (
      LOWER(COALESCE(job_posting_title, '')) LIKE '%cyber%security%'
      OR LOWER(COALESCE(job_posting_title, '')) LIKE '%security%engineer%'
  )
GROUP BY 1, 2, 3, 4
ORDER BY application_rows DESC, job_posting_title;
