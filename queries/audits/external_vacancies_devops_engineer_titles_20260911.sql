-- Propósito: validar con títulos de requisición externos que contienen
-- 'DevOps Engineer'. No devuelve IDs, candidatos ni texto libre.
-- Modo de entrega: presentation.
-- Regla de aceptación: al menos un título agrupado debe aparecer.

SELECT
  job_posting_title,
  'pass' AS external_devops_title_validation,
  CASE WHEN COUNT(*) >= 30 THEN COUNT(*) ELSE NULL END AS published_requisition_row_count
FROM hrda.requisitions_vw
WHERE job_posting_title ILIKE '%DevOps Engineer%'
  AND COALESCE(job_posted_externally, 0) = 1
GROUP BY job_posting_title
ORDER BY job_posting_title
LIMIT 20;
