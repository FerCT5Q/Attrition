-- Propósito: identificar únicamente los nombres de columnas de correo en
-- activos operativos de reclutamiento. No devuelve valores de correo.
-- Modo de entrega: presentation; metadatos solamente.

SELECT
  'hrda.' || table_name AS asset,
  column_name AS email_column,
  data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN (
    'requisitions', 'requisitions_vw',
    'applications', 'applications_vw',
    'job_applications', 'job_applications_vw',
    'interviews', 'interviews_vw'
  )
  AND LOWER(column_name) LIKE '%email%'
ORDER BY asset, email_column;
