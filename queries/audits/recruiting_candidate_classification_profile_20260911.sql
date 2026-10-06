-- Propósito: perfilar sólo los campos que podrían distinguir origen interno
-- o externo; no devuelve emails ni identificadores.
-- Modo de entrega: presentation.
-- Regla: cada grupo mostrado tiene >=30 filas y >=30 candidatos distintos.

SELECT
  'hrda.applications.candidate_type' AS field,
  COALESCE(candidate_type, '(null)') AS stored_value,
  COUNT(*) AS application_rows,
  COUNT(DISTINCT candidate_id) AS distinct_candidates
FROM hrda.applications
GROUP BY 1, 2
HAVING COUNT(*) >= 30 AND COUNT(DISTINCT candidate_id) >= 30

UNION ALL

SELECT
  'hrda.applications.source_category' AS field,
  COALESCE(source_category, '(null)') AS stored_value,
  COUNT(*) AS application_rows,
  COUNT(DISTINCT candidate_id) AS distinct_candidates
FROM hrda.applications
GROUP BY 1, 2
HAVING COUNT(*) >= 30 AND COUNT(DISTINCT candidate_id) >= 30

UNION ALL

SELECT
  'hrda.applications_vw.candidate_type' AS field,
  COALESCE(candidate_type, '(null)') AS stored_value,
  COUNT(*) AS application_rows,
  COUNT(DISTINCT candidate_id) AS distinct_candidates
FROM hrda.applications_vw
GROUP BY 1, 2
HAVING COUNT(*) >= 30 AND COUNT(DISTINCT candidate_id) >= 30

UNION ALL

SELECT
  'hrda.applications_vw.source_category' AS field,
  COALESCE(source_category, '(null)') AS stored_value,
  COUNT(*) AS application_rows,
  COUNT(DISTINCT candidate_id) AS distinct_candidates
FROM hrda.applications_vw
GROUP BY 1, 2
HAVING COUNT(*) >= 30 AND COUNT(DISTINCT candidate_id) >= 30

UNION ALL

SELECT
  'hrda.job_applications.source_category' AS field,
  COALESCE(source_category, '(null)') AS stored_value,
  COUNT(*) AS application_rows,
  COUNT(DISTINCT candidate_id) AS distinct_candidates
FROM hrda.job_applications
GROUP BY 1, 2
HAVING COUNT(*) >= 30 AND COUNT(DISTINCT candidate_id) >= 30

UNION ALL

SELECT
  'hrda.job_applications_vw.source_category' AS field,
  COALESCE(source_category, '(null)') AS stored_value,
  COUNT(*) AS application_rows,
  COUNT(DISTINCT candidate_id) AS distinct_candidates
FROM hrda.job_applications_vw
GROUP BY 1, 2
HAVING COUNT(*) >= 30 AND COUNT(DISTINCT candidate_id) >= 30

ORDER BY field, stored_value;
