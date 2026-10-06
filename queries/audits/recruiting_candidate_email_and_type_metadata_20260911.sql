-- Propósito: documentar metadatos de email y campos de clasificación de
-- candidatos en las fuentes de reclutamiento revisadas.
-- Modo de entrega: presentation; no devuelve valores personales.

SELECT
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN (
    'requisitions', 'requisitions_vw',
    'applications', 'applications_vw',
    'job_applications', 'job_applications_vw',
    'interviews', 'interviews_vw'
  )
  AND (
    LOWER(column_name) LIKE '%email%'
    OR LOWER(column_name) IN (
      'candidate_type', 'candidate_status', 'source_category', 'source',
      'job_posted_status', 'job_posted_internally_externally',
      'job_posted_externally', 'job_posted_internally'
    )
  )
ORDER BY table_name, ordinal_position;
