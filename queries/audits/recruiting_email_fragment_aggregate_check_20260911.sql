-- Propósito: revisar de forma agregada si algún campo de email de los
-- activos de reclutamiento contiene el fragmento solicitado.
-- Modo de entrega: presentation.
-- Privacidad: nunca devuelve direcciones ni filas individuales. Sólo publica
-- una coincidencia cuando el grupo tiene al menos 30 filas; las coincidencias
-- menores se clasifican como no reportables.

WITH matches AS (
  SELECT 'hrda.requisitions.hiring_manager_email' AS email_field, COUNT(*) AS matching_rows
  FROM hrda.requisitions
  WHERE hiring_manager_email ILIKE '%dianacc%'

  UNION ALL
  SELECT 'hrda.requisitions_vw.hiring_manager_email', COUNT(*)
  FROM hrda.requisitions_vw
  WHERE hiring_manager_email ILIKE '%dianacc%'

  UNION ALL
  SELECT 'hrda.applications.email', COUNT(*)
  FROM hrda.applications
  WHERE email ILIKE '%dianacc%'

  UNION ALL
  SELECT 'hrda.applications_vw.email', COUNT(*)
  FROM hrda.applications_vw
  WHERE email ILIKE '%dianacc%'

  UNION ALL
  SELECT 'hrda.job_applications.email', COUNT(*)
  FROM hrda.job_applications
  WHERE email ILIKE '%dianacc%'

  UNION ALL
  SELECT 'hrda.job_applications_vw.email', COUNT(*)
  FROM hrda.job_applications_vw
  WHERE email ILIKE '%dianacc%'

  UNION ALL
  SELECT 'hrda.interviews.candidate_email', COUNT(*)
  FROM hrda.interviews
  WHERE candidate_email ILIKE '%dianacc%'

  UNION ALL
  SELECT 'hrda.interviews.reviewer_email', COUNT(*)
  FROM hrda.interviews
  WHERE reviewer_email ILIKE '%dianacc%'

  UNION ALL
  SELECT 'hrda.interviews_vw.candidate_email', COUNT(*)
  FROM hrda.interviews_vw
  WHERE candidate_email ILIKE '%dianacc%'

  UNION ALL
  SELECT 'hrda.interviews_vw.reviewer_email', COUNT(*)
  FROM hrda.interviews_vw
  WHERE reviewer_email ILIKE '%dianacc%'
)
SELECT
  email_field,
  CASE
    WHEN matching_rows >= 30 THEN 'aggregate_match_reportable'
    ELSE 'not_reportable_under_privacy_threshold'
  END AS result,
  CASE WHEN matching_rows >= 30 THEN matching_rows ELSE NULL END AS matching_rows_if_ge_30
FROM matches
ORDER BY email_field;
