-- Propósito: localizar en HRDA las requisiciones mexicanas asociadas a las
-- tres vacantes solicitadas y resumir grado/ubicación; no devuelve IDs.
-- Modo de entrega: presentation.

SELECT
    CASE
        WHEN LOWER(COALESCE(job_posting_title, '')) LIKE '%database administrator%'
          OR LOWER(COALESCE(default_job_title, '')) LIKE '%database administrator%'
            THEN 'database_administrator'
        WHEN LOWER(COALESCE(job_posting_title, '')) LIKE '%cyber security engineer%'
          OR LOWER(COALESCE(default_job_title, '')) LIKE '%cyber security engineer%'
            THEN 'cyber_security_engineer_senior'
        WHEN LOWER(COALESCE(job_posting_title, '')) LIKE '%software developer%'
          OR LOWER(COALESCE(default_job_title, '')) LIKE '%software developer%'
            THEN 'software_developer_senior'
    END AS requested_role,
    job_posting_title,
    default_job_title,
    job_requisition_primary_location,
    country,
    compensation_grade,
    requisition_compensation_grade_profile,
    job_code,
    COUNT(*) AS requisition_rows
FROM hrda.requisitions_vw
WHERE LOWER(COALESCE(country, '')) LIKE '%mex%'
  AND (
      LOWER(COALESCE(job_posting_title, '')) LIKE '%database administrator%'
      OR LOWER(COALESCE(default_job_title, '')) LIKE '%database administrator%'
      OR LOWER(COALESCE(job_posting_title, '')) LIKE '%cyber security engineer%'
      OR LOWER(COALESCE(default_job_title, '')) LIKE '%cyber security engineer%'
      OR LOWER(COALESCE(job_posting_title, '')) LIKE '%software developer%'
      OR LOWER(COALESCE(default_job_title, '')) LIKE '%software developer%'
  )
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
ORDER BY requested_role, requisition_rows DESC;
