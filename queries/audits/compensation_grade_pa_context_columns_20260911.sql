-- Propósito: mostrar columnas de contexto alrededor de los campos de
-- compensation grade en activos de reclutamiento; sólo metadatos.

SELECT
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN (
    'job_applications', 'job_applications_vw',
    'applications', 'applications_vw'
  )
ORDER BY table_name, ordinal_position;
