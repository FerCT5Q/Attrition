-- Propósito: comprobar si las tablas de aplicaciones contienen una
-- clasificación agregada de candidato interno/externo.
-- Modo de entrega: presentation; no devuelve emails ni IDs.
-- Regla: sólo publicar grupos con >=30 filas y >=30 candidatos distintos.
-- El grain es de aplicaciones/filas de proceso, no necesariamente de persona.

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
  'hrda.applications.source' AS field,
  COALESCE(source, '(null)') AS stored_value,
  COUNT(*) AS application_rows,
  COUNT(DISTINCT candidate_id) AS distinct_candidates
FROM hrda.applications
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
  'hrda.job_applications.source' AS field,
  COALESCE(source, '(null)') AS stored_value,
  COUNT(*) AS application_rows,
  COUNT(DISTINCT candidate_id) AS distinct_candidates
FROM hrda.job_applications
GROUP BY 1, 2
HAVING COUNT(*) >= 30 AND COUNT(DISTINCT candidate_id) >= 30

ORDER BY field, stored_value;
