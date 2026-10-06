-- Propósito: comprobar todas las variantes mexicanas de títulos de
-- cybersecurity y su grade, evitando inferir Senior/Staff por similitud.
-- Modo de entrega: presentation; sin IDs de requisición.

SELECT
    job_posting_title,
    default_job_title,
    job_requisition_primary_location,
    country,
    compensation_grade,
    requisition_compensation_grade_profile,
    job_code,
    COUNT(*) AS requisition_rows
FROM hrda.requisitions_vw
WHERE LOWER(COALESCE(country, '')) = 'mexico'
  AND (
      LOWER(COALESCE(job_posting_title, '')) LIKE '%security%'
      OR LOWER(COALESCE(default_job_title, '')) LIKE '%security%'
      OR LOWER(COALESCE(job_posting_title, '')) LIKE '%cyber%'
      OR LOWER(COALESCE(default_job_title, '')) LIKE '%cyber%'
  )
GROUP BY 1, 2, 3, 4, 5, 6, 7
ORDER BY requisition_rows DESC, job_posting_title;
