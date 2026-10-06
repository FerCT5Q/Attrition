-- Claim: identificar en qué activos operativos aparece el título exacto
-- 'DevOps Engineer (Cloud & CI/CD Platforms)'.
-- Deliverable mode: presentation; aggregate presence only.
-- Acceptance rule: una tabla contiene el título si su conteo agregado es > 0.
-- Nunca se seleccionan valores de correo, candidatos, identificadores o texto libre.

WITH title_presence AS (
  SELECT 'hrda.requisitions' AS asset,
    CASE WHEN COUNT(*) > 0 THEN 'present' ELSE 'absent' END AS title_presence
  FROM hrda.requisitions
  WHERE job_posting_title = 'DevOps Engineer (Cloud & CI/CD Platforms)'

  UNION ALL

  SELECT 'hrda.requisitions_vw' AS asset,
    CASE WHEN COUNT(*) > 0 THEN 'present' ELSE 'absent' END AS title_presence
  FROM hrda.requisitions_vw
  WHERE job_posting_title = 'DevOps Engineer (Cloud & CI/CD Platforms)'

  UNION ALL

  SELECT 'hrda.applications' AS asset,
    CASE WHEN COUNT(*) > 0 THEN 'present' ELSE 'absent' END AS title_presence
  FROM hrda.applications
  WHERE job_posting_title = 'DevOps Engineer (Cloud & CI/CD Platforms)'

  UNION ALL

  SELECT 'hrda.applications_vw' AS asset,
    CASE WHEN COUNT(*) > 0 THEN 'present' ELSE 'absent' END AS title_presence
  FROM hrda.applications_vw
  WHERE job_posting_title = 'DevOps Engineer (Cloud & CI/CD Platforms)'

  UNION ALL

  SELECT 'hrda.job_applications' AS asset,
    CASE WHEN COUNT(*) > 0 THEN 'present' ELSE 'absent' END AS title_presence
  FROM hrda.job_applications
  WHERE job_posting_title = 'DevOps Engineer (Cloud & CI/CD Platforms)'

  UNION ALL

  SELECT 'hrda.job_applications_vw' AS asset,
    CASE WHEN COUNT(*) > 0 THEN 'present' ELSE 'absent' END AS title_presence
  FROM hrda.job_applications_vw
  WHERE job_posting_title = 'DevOps Engineer (Cloud & CI/CD Platforms)'
)
SELECT
  asset,
  title_presence
FROM title_presence
ORDER BY asset;
