-- Propósito: confirmar las columnas de título, audiencia externa y estado
-- en los activos vigentes de requisiciones y aplicaciones.
-- Modo de entrega: presentation. Sólo devuelve metadatos.

SELECT
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN (
    'requisitions', 'requisitions_vw',
    'applications', 'applications_vw', 'applications_latest_mvw',
    'job_applications', 'job_applications_vw',
    'vndly_requisition'
  )
  AND (
    LOWER(column_name) LIKE '%title%'
    OR LOWER(column_name) LIKE '%requisition%'
    OR LOWER(column_name) LIKE '%external%'
    OR LOWER(column_name) LIKE '%internal%'
    OR LOWER(column_name) LIKE '%posting%'
    OR LOWER(column_name) LIKE '%status%'
    OR LOWER(column_name) LIKE '%open%'
    OR LOWER(column_name) LIKE '%close%'
    OR LOWER(column_name) LIKE '%candidate%'
    OR LOWER(column_name) LIKE '%source%'
    OR LOWER(column_name) LIKE '%job%'
  )
ORDER BY table_name, ordinal_position;
